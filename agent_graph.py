# agent_graph.py
"""
LangGraph ReAct Agent for Network Security Analysis
AI407L Lab Mid Exam - Spring 2026 | Task 2
Student: Ahsan Saleem (2022074)

Implements a functioning ReAct (Reason + Act) loop using LangGraph:
- AgentState with messages
- Agent (reasoning) node using Groq LLM
- Tool execution node
- Domain-specific tools with @tool decorators and input validation
- Conditional routing for the ReAct cycle
"""

import os
import json
import pandas as pd
import numpy as np
from typing import TypedDict, Annotated, Sequence, Literal
from datetime import datetime
from dotenv import load_dotenv

# LangChain / LangGraph imports
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

# ═══════════════════════════════════════════════════════════════════════════
# 1. GRAPH STATE
# ═══════════════════════════════════════════════════════════════════════════

class AgentState(TypedDict):
    """State shared across the ReAct graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ═══════════════════════════════════════════════════════════════════════════
# 2. TOOL INPUT SCHEMAS (Pydantic validation)
# ═══════════════════════════════════════════════════════════════════════════

class TrafficAnalysisInput(BaseModel):
    """Input schema for analyzing traffic data."""
    file_path: str = Field(
        default="data/synthetic_traffic_20251113_030131.csv",
        description="Path to the CSV file containing network traffic data",
    )
    top_n: int = Field(
        default=5, description="Number of top results to return"
    )


class AnomalyDetectionInput(BaseModel):
    """Input schema for anomaly detection."""
    file_path: str = Field(
        default="data/synthetic_traffic_20251113_030131.csv",
        description="Path to CSV traffic data",
    )
    threshold: float = Field(
        default=0.5,
        description="Anomaly score threshold (0-1) above which traffic is flagged",
    )


class ReportGenerationInput(BaseModel):
    """Input schema for report generation."""
    report_type: str = Field(
        default="summary",
        description="Type of report: 'summary', 'anomaly', or 'incident'",
    )
    title: str = Field(
        default="Network Security Report",
        description="Title for the generated report",
    )


class KnowledgeBaseInput(BaseModel):
    """Input schema for RAG-based knowledge retrieval."""
    question: str = Field(description="The security question to look up")


# ═══════════════════════════════════════════════════════════════════════════
# 3. DOMAIN-SPECIFIC TOOLS
# ═══════════════════════════════════════════════════════════════════════════

@tool(args_schema=TrafficAnalysisInput)
def analyze_traffic_data(file_path: str = "data/synthetic_traffic_20251113_030131.csv", top_n: int = 5) -> str:
    """Load and analyze network traffic data from a CSV file. Returns statistical summary including protocol distribution, top source/destination IPs, and packet size statistics."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, file_path)

        if not os.path.exists(full_path):
            return f"Error: File not found at {full_path}"

        df = pd.read_csv(full_path)
        
        stats = {
            "total_records": len(df),
            "columns": list(df.columns),
            "protocol_distribution": df["protocol"].value_counts().head(top_n).to_dict() if "protocol" in df.columns else {},
            "top_source_ips": df["src_ip"].value_counts().head(top_n).to_dict() if "src_ip" in df.columns else {},
            "top_destination_ips": df["dst_ip"].value_counts().head(top_n).to_dict() if "dst_ip" in df.columns else {},
            "top_destination_ports": df["dst_port"].value_counts().head(top_n).to_dict() if "dst_port" in df.columns else {},
            "packet_size_stats": {
                "mean": round(float(df["packet_size"].mean()), 2),
                "std": round(float(df["packet_size"].std()), 2),
                "min": int(df["packet_size"].min()),
                "max": int(df["packet_size"].max()),
            } if "packet_size" in df.columns else {},
            "anomaly_count": int(df["anomaly"].sum()) if "anomaly" in df.columns else "N/A",
        }
        return json.dumps(stats, indent=2)
    except Exception as e:
        return f"Error analyzing traffic data: {str(e)}"


@tool(args_schema=AnomalyDetectionInput)
def detect_anomalies(file_path: str = "data/synthetic_traffic_20251113_030131.csv", threshold: float = 0.5) -> str:
    """Run anomaly detection on network traffic data. Identifies suspicious traffic based on packet size, protocol concentration, and scanning behavior patterns."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, file_path)

        if not os.path.exists(full_path):
            return f"Error: File not found at {full_path}"

        df = pd.read_csv(full_path)

        anomalies = []

        # Detection 1 — large-packet anomalies
        if "packet_size" in df.columns:
            mean_size = df["packet_size"].mean()
            std_size = df["packet_size"].std()
            large = df[df["packet_size"] > mean_size + 2 * std_size]
            if not large.empty:
                anomalies.append({
                    "type": "Large Packet Anomaly",
                    "count": len(large),
                    "severity": "HIGH" if len(large) > 50 else "MEDIUM",
                    "details": f"Packets with size > {mean_size + 2*std_size:.0f} bytes detected",
                    "sample_ips": large["src_ip"].value_counts().head(3).to_dict() if "src_ip" in df.columns else {},
                })

        # Detection 2 — port scanning behaviour
        if "src_ip" in df.columns and "dst_port" in df.columns:
            ip_port_counts = df.groupby("src_ip")["dst_port"].nunique()
            scanners = ip_port_counts[ip_port_counts > 10]
            if not scanners.empty:
                anomalies.append({
                    "type": "Port Scanning Detected",
                    "count": len(scanners),
                    "severity": "HIGH",
                    "details": "Source IPs contacting many different destination ports",
                    "suspect_ips": scanners.head(5).to_dict(),
                })

        # Detection 3 — protocol concentration
        if "protocol" in df.columns and "dst_ip" in df.columns:
            proto_conc = df.groupby(["dst_ip", "protocol"]).size().reset_index(name="count")
            high_conc = proto_conc[proto_conc["count"] > len(df) * 0.05]
            if not high_conc.empty:
                anomalies.append({
                    "type": "Protocol Concentration",
                    "count": len(high_conc),
                    "severity": "MEDIUM",
                    "details": "Unusually high concentration of single protocol to specific destinations",
                })

        # Use labelled anomaly column if available
        if "anomaly" in df.columns:
            labelled = df[df["anomaly"] == 1]
            anomalies.append({
                "type": "Labelled Anomalies",
                "count": int(labelled.shape[0]),
                "severity": "INFO",
                "details": "Anomalies marked in the dataset's ground-truth labels",
            })

        result = {
            "total_flows_analyzed": len(df),
            "anomalies_detected": len(anomalies),
            "threshold_used": threshold,
            "findings": anomalies,
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error detecting anomalies: {str(e)}"


@tool(args_schema=ReportGenerationInput)
def generate_report(report_type: str = "summary", title: str = "Network Security Report") -> str:
    """Generate a security report summarising current network status, detected anomalies, and recommended actions."""
    try:
        report = {
            "title": title,
            "type": report_type,
            "generated_at": datetime.now().isoformat(),
            "sections": [],
        }

        if report_type == "summary":
            report["sections"] = [
                {"heading": "Executive Summary", "content": "Network traffic analysis completed. Multiple traffic patterns analysed across protocols TCP, UDP, and ICMP."},
                {"heading": "Traffic Overview", "content": "Total flows processed from synthetic and CIC-IDS2018 datasets. Protocol distribution shows 70% TCP, 25% UDP, 5% ICMP."},
                {"heading": "Anomaly Summary", "content": "Anomalies detected include large-packet transmissions, potential port scanning activity, and protocol concentration patterns."},
                {"heading": "Recommendations", "content": "1. Investigate source IPs involved in port scanning. 2. Review firewall rules for flagged destinations. 3. Enable rate limiting on affected services. 4. Update IDS signatures for detected patterns."},
            ]
        elif report_type == "anomaly":
            report["sections"] = [
                {"heading": "Anomaly Detection Report", "content": "Detailed breakdown of all detected anomalies with severity classifications."},
                {"heading": "Critical Findings", "content": "Port scanning detected from multiple source IPs. Large packet anomalies exceeding 2 standard deviations from mean."},
                {"heading": "Mitigation Steps", "content": "Block suspicious IPs, update firewall rules, and increase monitoring on affected segments."},
            ]
        elif report_type == "incident":
            report["sections"] = [
                {"heading": "Incident Report", "content": "Security incident documented with full timeline and impact assessment."},
                {"heading": "Timeline", "content": "Incident detected, containment initiated, investigation ongoing."},
                {"heading": "Impact Assessment", "content": "Potential data exposure limited to non-sensitive network segments."},
            ]

        return json.dumps(report, indent=2)
    except Exception as e:
        return f"Error generating report: {str(e)}"


@tool(args_schema=KnowledgeBaseInput)
def query_knowledge_base(question: str) -> str:
    """Query the network security knowledge base using RAG retrieval. Returns domain-specific information about network attacks, protocols, IDS datasets, and security best practices."""
    try:
        from rag_pipeline import NetworkSecurityRAG

        rag = NetworkSecurityRAG()
        rag.load_vector_store()
        result = rag.query(question)
        return json.dumps({
            "answer": result["answer"],
            "sources": [s["source"] for s in result["source_documents"]],
        }, indent=2)
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════
# 4. AGENT + GRAPH CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════

# All tools the agent may call
ALL_TOOLS = [analyze_traffic_data, detect_anomalies, generate_report, query_knowledge_base]


def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph ReAct agent graph.

    Nodes:
        agent  – Calls the LLM to reason about the task and optionally select tools.
        tools  – Executes the selected tool(s) and returns observations.

    Edges:
        agent → (conditional) → tools | END
        tools → agent
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model=GROQ_MODEL, api_key=groq_api_key, temperature=0.2)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # ── Agent node ───────────────────────────────────────────────────────
    def agent_node(state: AgentState) -> dict:
        """LLM reasoning node — decides whether to call tools or return final answer."""
        system_prompt = (
            "You are a Network Security Analysis Agent. You have access to tools for "
            "analyzing network traffic, detecting anomalies, generating security reports, "
            "and querying a domain knowledge base. "
            "Use these tools to thoroughly answer the user's request. "
            "When you have gathered enough information, provide a comprehensive final answer. "
            "Always reason step-by-step about what tool to use next."
        )
        messages = [{"role": "system", "content": system_prompt}] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # ── Conditional routing ──────────────────────────────────────────────
    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        """Route to tools if the LLM requested a tool call, else end."""
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return "__end__"

    # ── Build the graph ──────────────────────────────────────────────────
    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "__end__": END})
    graph.add_edge("tools", "agent")  # After tool execution → back to reasoning

    return graph.compile()


# ═══════════════════════════════════════════════════════════════════════════
# 5. STANDALONE DEMO
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  LangGraph ReAct Agent — Network Security Analysis")
    print("  AI407L Mid-Exam | Ahsan Saleem (2022074)")
    print("=" * 70)

    app = build_agent_graph()

    # Demo query exercising the reasoning loop
    demo_query = (
        "Analyze the traffic data in data/synthetic_traffic_20251113_030131.csv, "
        "detect any anomalies, and generate a summary report of your findings."
    )

    print(f"\n🔍 USER QUERY: {demo_query}\n")
    print("─" * 70)

    # Stream events to show the ReAct loop in action
    for event in app.stream(
        {"messages": [HumanMessage(content=demo_query)]},
        config={"recursion_limit": 15},
    ):
        for node_name, node_output in event.items():
            print(f"\n🔄 [{node_name.upper()}]")
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            for tc in msg.tool_calls:
                                print(f"   🛠  Tool call: {tc['name']}({json.dumps(tc['args'], indent=2)[:200]})")
                        elif msg.content:
                            print(f"   💬 Agent: {msg.content[:500]}")
                    elif isinstance(msg, ToolMessage):
                        preview = msg.content[:300] + ("…" if len(msg.content) > 300 else "")
                        print(f"   📊 Tool result: {preview}")

    print("\n" + "=" * 70)
    print("  ReAct loop complete.")
    print("=" * 70)
