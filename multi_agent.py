# multi_agent.py
"""
Multi-Agent Orchestration for Network Security
AI407L Lab Mid Exam - Spring 2026 | Task 3
Student: Ahsan Saleem (2022074)

Implements multi-agent architecture using LangGraph:
- Security Analyst Agent: threat detection & analysis (restricted tools)
- Incident Responder Agent: response actions & reporting (restricted tools)
- Supervisor Router: routes tasks based on intent
- State handover between agents with collaborative execution
"""

import os
import json
from typing import TypedDict, Annotated, Sequence, Literal, List
from datetime import datetime
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"


# ═══════════════════════════════════════════════════════════════════════════
# 1. MULTI-AGENT STATE
# ═══════════════════════════════════════════════════════════════════════════

class MultiAgentState(TypedDict):
    """State shared across multiple agents."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: str          # which agent is active
    findings: str               # analyst findings handed to responder
    task_complete: bool


# ═══════════════════════════════════════════════════════════════════════════
# 2. ANALYST-ONLY TOOLS
# ═══════════════════════════════════════════════════════════════════════════

class AnalyzeTrafficInput(BaseModel):
    file_path: str = Field(default="data/synthetic_traffic_20251113_030131.csv", description="CSV file path")

class DetectAnomaliesInput(BaseModel):
    file_path: str = Field(default="data/synthetic_traffic_20251113_030131.csv", description="CSV file path")

class QueryKBInput(BaseModel):
    question: str = Field(description="Security question")


@tool(args_schema=AnalyzeTrafficInput)
def analyst_analyze_traffic(file_path: str = "data/synthetic_traffic_20251113_030131.csv") -> str:
    """[ANALYST TOOL] Analyze network traffic data and return statistical summary."""
    import pandas as pd
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(base, file_path))
        stats = {
            "total_records": len(df),
            "protocols": df["protocol"].value_counts().to_dict() if "protocol" in df.columns else {},
            "top_src_ips": df["src_ip"].value_counts().head(5).to_dict() if "src_ip" in df.columns else {},
            "top_dst_ports": df["dst_port"].value_counts().head(5).to_dict() if "dst_port" in df.columns else {},
            "packet_size_mean": round(float(df["packet_size"].mean()), 2) if "packet_size" in df.columns else 0,
            "anomaly_count": int(df["anomaly"].sum()) if "anomaly" in df.columns else 0,
        }
        return json.dumps(stats, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=DetectAnomaliesInput)
def analyst_detect_anomalies(file_path: str = "data/synthetic_traffic_20251113_030131.csv") -> str:
    """[ANALYST TOOL] Detect anomalies in network traffic using statistical analysis."""
    import pandas as pd
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(base, file_path))
        findings = []

        if "packet_size" in df.columns:
            mean_s, std_s = df["packet_size"].mean(), df["packet_size"].std()
            large = df[df["packet_size"] > mean_s + 2*std_s]
            if len(large):
                findings.append({"type": "Large Packet", "count": len(large), "severity": "HIGH",
                                 "suspect_ips": large["src_ip"].value_counts().head(3).to_dict() if "src_ip" in df.columns else {}})

        if "src_ip" in df.columns and "dst_port" in df.columns:
            scanners = df.groupby("src_ip")["dst_port"].nunique()
            scans = scanners[scanners > 10]
            if len(scans):
                findings.append({"type": "Port Scanning", "count": len(scans), "severity": "HIGH",
                                 "suspect_ips": scans.head(3).to_dict()})

        if "anomaly" in df.columns:
            findings.append({"type": "Labelled Anomalies", "count": int(df["anomaly"].sum()), "severity": "INFO"})

        return json.dumps({"findings": findings, "total_analyzed": len(df)}, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=QueryKBInput)
def analyst_query_kb(question: str) -> str:
    """[ANALYST TOOL] Query network security knowledge base for domain expertise."""
    try:
        from rag_pipeline import NetworkSecurityRAG
        rag = NetworkSecurityRAG()
        rag.load_vector_store()
        result = rag.query(question)
        return json.dumps({"answer": result["answer"][:500], "sources": [s["source"] for s in result["source_documents"]]}, indent=2)
    except Exception as e:
        return f"KB Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# 3. RESPONDER-ONLY TOOLS
# ═══════════════════════════════════════════════════════════════════════════

class ReportInput(BaseModel):
    title: str = Field(default="Incident Response Report", description="Report title")
    findings_summary: str = Field(default="", description="Summary of analyst findings")

class BlockIPInput(BaseModel):
    ip_address: str = Field(description="IP address to block")
    reason: str = Field(description="Reason for blocking")

class RecommendInput(BaseModel):
    threat_type: str = Field(description="Type of threat detected")
    severity: str = Field(default="HIGH", description="Threat severity: LOW, MEDIUM, HIGH, CRITICAL")


@tool(args_schema=ReportInput)
def responder_generate_report(title: str = "Incident Response Report", findings_summary: str = "") -> str:
    """[RESPONDER TOOL] Generate a formal incident response report based on analyst findings."""
    report = {
        "title": title,
        "generated_at": datetime.now().isoformat(),
        "findings_summary": findings_summary,
        "sections": [
            {"heading": "Incident Summary", "content": f"Automated analysis detected threats requiring response. {findings_summary}"},
            {"heading": "Response Actions", "content": "1. Flagged IPs have been queued for blocking. 2. Firewall rules updated. 3. Monitoring enhanced on affected segments."},
            {"heading": "Recommendations", "content": "1. Review flagged IPs within 24 hours. 2. Update IDS signatures. 3. Conduct forensic analysis on affected endpoints."},
        ],
    }
    return json.dumps(report, indent=2)


@tool(args_schema=BlockIPInput)
def responder_block_ip(ip_address: str, reason: str) -> str:
    """[RESPONDER TOOL] Block a suspicious IP address (HIGH-RISK action — would require approval in production)."""
    action = {
        "action": "BLOCK_IP",
        "ip_address": ip_address,
        "reason": reason,
        "status": "EXECUTED",
        "timestamp": datetime.now().isoformat(),
        "note": "IP added to firewall deny list",
    }
    return json.dumps(action, indent=2)


@tool(args_schema=RecommendInput)
def responder_recommend_action(threat_type: str, severity: str = "HIGH") -> str:
    """[RESPONDER TOOL] Generate specific recommended actions based on threat type and severity."""
    recs = {
        "Port Scanning": ["Block source IP at firewall", "Enable port-scan detection on IDS", "Review target services for vulnerabilities"],
        "Large Packet": ["Implement packet-size filtering", "Check for data exfiltration", "Monitor source IPs for further anomalies"],
        "DDoS": ["Activate DDoS mitigation", "Enable rate limiting", "Contact upstream ISP for traffic scrubbing"],
        "Brute Force": ["Enforce account lockout policies", "Implement MFA", "Block attacker IPs"],
    }
    actions = recs.get(threat_type, ["Investigate further", "Increase monitoring", "Update signatures"])
    result = {
        "threat_type": threat_type,
        "severity": severity,
        "recommended_actions": actions,
        "priority": "IMMEDIATE" if severity in ("HIGH", "CRITICAL") else "SCHEDULED",
    }
    return json.dumps(result, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# 4. AGENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

ANALYST_TOOLS = [analyst_analyze_traffic, analyst_detect_anomalies, analyst_query_kb]
RESPONDER_TOOLS = [responder_generate_report, responder_block_ip, responder_recommend_action]

groq_key = os.getenv("GROQ_API_KEY")
analyst_llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0.2).bind_tools(ANALYST_TOOLS)
responder_llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0.2).bind_tools(RESPONDER_TOOLS)
supervisor_llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0.1)


# ═══════════════════════════════════════════════════════════════════════════
# 5. NODE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def supervisor_node(state: MultiAgentState) -> dict:
    """Supervisor decides which agent should handle the task next."""
    sys_prompt = (
        "You are a Security Operations Supervisor. Based on the conversation so far, decide:\n"
        "- If the task needs ANALYSIS (traffic analysis, anomaly detection, knowledge lookup) → respond with exactly: ROUTE_TO_ANALYST\n"
        "- If analysis is done and findings need RESPONSE (reporting, blocking, recommendations) → respond with exactly: ROUTE_TO_RESPONDER\n"
        "- If the task is fully complete → respond with exactly: TASK_COMPLETE\n"
        "Respond with ONLY one of those three directives, nothing else."
    )
    msgs = [SystemMessage(content=sys_prompt)] + list(state["messages"])
    response = supervisor_llm.invoke(msgs)
    return {"messages": [response], "current_agent": response.content.strip()}


def analyst_node(state: MultiAgentState) -> dict:
    """Security Analyst agent — analyses traffic and detects threats."""
    sys_prompt = (
        "You are the Security Analyst Agent. Your role is to analyze network traffic data, "
        "detect anomalies, and query the knowledge base for context. Use your available tools "
        "to conduct thorough analysis. Summarize your findings clearly for the Incident Responder."
    )
    msgs = [SystemMessage(content=sys_prompt)] + list(state["messages"])
    response = analyst_llm.invoke(msgs)
    return {"messages": [response]}


def responder_node(state: MultiAgentState) -> dict:
    """Incident Responder agent — generates reports and takes actions."""
    sys_prompt = (
        "You are the Incident Responder Agent. The Security Analyst has completed their analysis. "
        "Your role is to: 1) Generate an incident report, 2) Recommend specific actions based on findings, "
        "3) Block suspicious IPs if warranted. Use your tools to take appropriate response actions."
    )
    msgs = [SystemMessage(content=sys_prompt)] + list(state["messages"])
    response = responder_llm.invoke(msgs)
    return {"messages": [response]}


# ═══════════════════════════════════════════════════════════════════════════
# 6. ROUTING LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def supervisor_router(state: MultiAgentState) -> str:
    """Route based on supervisor decision."""
    current = state.get("current_agent", "")
    if "ROUTE_TO_ANALYST" in current:
        return "analyst"
    elif "ROUTE_TO_RESPONDER" in current:
        return "responder"
    else:
        return "__end__"


def agent_should_continue(state: MultiAgentState) -> str:
    """Check if the current agent wants to call tools."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "supervisor"


def responder_should_continue(state: MultiAgentState) -> str:
    """Check if responder wants to call tools."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "responder_tools"
    return "supervisor"


# ═══════════════════════════════════════════════════════════════════════════
# 7. BUILD THE MULTI-AGENT GRAPH
# ═══════════════════════════════════════════════════════════════════════════

def build_multi_agent_graph():
    """Build the multi-agent LangGraph with supervisor routing."""
    analyst_tool_node = ToolNode(ANALYST_TOOLS)
    responder_tool_node = ToolNode(RESPONDER_TOOLS)

    graph = StateGraph(MultiAgentState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("tools", analyst_tool_node)          # analyst's tools
    graph.add_node("responder", responder_node)
    graph.add_node("responder_tools", responder_tool_node)  # responder's tools

    # Entry
    graph.set_entry_point("supervisor")

    # Supervisor → route to analyst / responder / end
    graph.add_conditional_edges("supervisor", supervisor_router,
                                {"analyst": "analyst", "responder": "responder", "__end__": END})

    # Analyst → tools or back to supervisor
    graph.add_conditional_edges("analyst", agent_should_continue,
                                {"tools": "tools", "supervisor": "supervisor"})
    graph.add_edge("tools", "analyst")

    # Responder → tools or back to supervisor
    graph.add_conditional_edges("responder", responder_should_continue,
                                {"responder_tools": "responder_tools", "supervisor": "supervisor"})
    graph.add_edge("responder_tools", "responder")

    return graph.compile()


# ═══════════════════════════════════════════════════════════════════════════
# 8. STANDALONE DEMO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  Multi-Agent Orchestration — Security Operations")
    print("  AI407L Mid-Exam | Ahsan Saleem (2022074)")
    print("=" * 70)

    app = build_multi_agent_graph()

    query = (
        "Analyze the network traffic in data/synthetic_traffic_20251113_030131.csv, "
        "detect any anomalies, then generate a full incident response report with "
        "recommended actions for any threats found."
    )

    print(f"\n🔍 USER QUERY: {query}\n")
    print("─" * 70)

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "current_agent": "",
        "findings": "",
        "task_complete": False,
    }

    for event in app.stream(initial_state, config={"recursion_limit": 25}):
        for node_name, node_output in event.items():
            agent_label = {
                "supervisor": "🎯 SUPERVISOR",
                "analyst": "🔬 ANALYST",
                "tools": "🛠  ANALYST TOOLS",
                "responder": "🛡  RESPONDER",
                "responder_tools": "🛠  RESPONDER TOOLS",
            }.get(node_name, node_name.upper())

            print(f"\n{agent_label}")

            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            for tc in msg.tool_calls:
                                print(f"   → Tool: {tc['name']}({json.dumps(tc['args'])[:150]})")
                        elif msg.content:
                            content = msg.content[:400]
                            print(f"   💬 {content}")
                    elif isinstance(msg, ToolMessage):
                        print(f"   📊 Result: {msg.content[:200]}…")

    print("\n" + "=" * 70)
    print("  Multi-agent execution complete.")
    print("=" * 70)
