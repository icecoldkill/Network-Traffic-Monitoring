# hitl_agent.py
"""
Persistent Memory & Human-in-the-Loop (HITL) Agent
AI407L Lab Mid Exam - Spring 2026 | Task 4
Student: Ahsan Saleem (2022074)

Implements:
- Persistent state management using LangGraph MemorySaver checkpointer
- Session recovery via thread identifiers
- High-risk tool (block_ip_address) with safety interruption
- Human approval/rejection/edit flow before executing dangerous actions
"""

import os
import json
from typing import TypedDict, Annotated, Sequence, Literal
from datetime import datetime
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
)
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"


# ═══════════════════════════════════════════════════════════════════════════
# 1. GRAPH STATE
# ═══════════════════════════════════════════════════════════════════════════

class HITLState(TypedDict):
    """State for the HITL agent with persistent memory."""
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ═══════════════════════════════════════════════════════════════════════════
# 2. TOOLS — including the HIGH-RISK tool
# ═══════════════════════════════════════════════════════════════════════════

class AnalyzeInput(BaseModel):
    file_path: str = Field(default="data/synthetic_traffic_20251113_030131.csv")

class BlockIPInput(BaseModel):
    ip_address: str = Field(description="IP address to block")
    reason: str = Field(description="Reason for blocking this IP")
    duration_hours: int = Field(default=24, description="Duration of block in hours")

class CheckStatusInput(BaseModel):
    ip_address: str = Field(default="", description="Optional: check status of specific IP")


@tool(args_schema=AnalyzeInput)
def analyze_traffic(file_path: str = "data/synthetic_traffic_20251113_030131.csv") -> str:
    """Analyze network traffic data and identify suspicious IPs."""
    import pandas as pd
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(base, file_path))
        
        suspicious = []
        if "src_ip" in df.columns and "dst_port" in df.columns:
            scanners = df.groupby("src_ip")["dst_port"].nunique()
            for ip, count in scanners[scanners > 10].items():
                suspicious.append({"ip": ip, "reason": f"Port scanning — contacted {count} unique ports", "severity": "HIGH"})
        
        if "packet_size" in df.columns and "src_ip" in df.columns:
            mean_s, std_s = df["packet_size"].mean(), df["packet_size"].std()
            large = df[df["packet_size"] > mean_s + 2*std_s]
            for ip in large["src_ip"].unique()[:3]:
                if not any(s["ip"] == ip for s in suspicious):
                    suspicious.append({"ip": ip, "reason": "Sending abnormally large packets", "severity": "MEDIUM"})
        
        return json.dumps({"total_flows": len(df), "suspicious_ips": suspicious}, indent=2)
    except Exception as e:
        return f"Error: {e}"


@tool(args_schema=BlockIPInput)
def block_ip_address(ip_address: str, reason: str, duration_hours: int = 24) -> str:
    """⚠️ HIGH-RISK ACTION: Block an IP address at the firewall. This action will immediately deny all traffic from the specified IP. Requires human approval before execution."""
    # This is the high-risk tool that triggers HITL interrupt
    action = {
        "action": "BLOCK_IP",
        "ip_address": ip_address,
        "reason": reason,
        "duration_hours": duration_hours,
        "status": "BLOCKED",
        "executed_at": datetime.now().isoformat(),
        "firewall_rule": f"iptables -A INPUT -s {ip_address} -j DROP",
        "auto_unblock_at": f"In {duration_hours} hours",
    }
    return json.dumps(action, indent=2)


@tool(args_schema=CheckStatusInput)
def check_network_status(ip_address: str = "") -> str:
    """Check current network and firewall status."""
    status = {
        "network_status": "operational",
        "active_blocks": 3,
        "total_flows_today": 150000,
        "alerts_pending": 7,
        "timestamp": datetime.now().isoformat(),
    }
    if ip_address:
        status["ip_status"] = {"ip": ip_address, "blocked": False, "last_seen": "2 minutes ago"}
    return json.dumps(status, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
# 3. HITL AGENT GRAPH
# ═══════════════════════════════════════════════════════════════════════════

ALL_TOOLS = [analyze_traffic, block_ip_address, check_network_status]
# block_ip_address is the HIGH-RISK tool that requires human approval


def build_hitl_graph():
    """
    Build agent graph with:
    - MemorySaver checkpointer for persistent state
    - interrupt_before on the tools node when block_ip_address is called
    """
    groq_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model=GROQ_MODEL, api_key=groq_key, temperature=0.2)
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # ── Agent node ───────────────────────────────────────────────────────
    def agent_node(state: HITLState) -> dict:
        sys_prompt = (
            "You are a Network Security Agent with persistent memory. You can analyze traffic, "
            "check network status, and block suspicious IP addresses.\n\n"
            "IMPORTANT: When you determine an IP should be blocked, call the block_ip_address tool. "
            "This is a HIGH-RISK action and the system will pause for human approval before executing.\n\n"
            "Always explain your reasoning before proposing to block an IP."
        )
        msgs = [SystemMessage(content=sys_prompt)] + list(state["messages"])
        response = llm_with_tools.invoke(msgs)
        return {"messages": [response]}

    # ── Conditional routing ──────────────────────────────────────────────
    def should_continue(state: HITLState) -> Literal["tools", "__end__"]:
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return "__end__"

    # ── Build graph ──────────────────────────────────────────────────────
    tool_node = ToolNode(ALL_TOOLS)
    checkpointer = MemorySaver()

    graph = StateGraph(HITLState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "__end__": END})
    graph.add_edge("tools", "agent")

    # Compile with checkpointer AND interrupt_before on tools node
    # This means when the agent calls a tool, the graph pauses for human review
    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["tools"],  # Pause before executing ANY tool for HITL
    )

    return compiled, checkpointer


# ═══════════════════════════════════════════════════════════════════════════
# 4. HUMAN-IN-THE-LOOP INTERACTION
# ═══════════════════════════════════════════════════════════════════════════

def display_pending_action(state):
    """Display the tool call that's pending human approval."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        for tc in last_msg.tool_calls:
            print("\n" + "⚠" * 35)
            print("  ⚠️  HUMAN APPROVAL REQUIRED  ⚠️")
            print("⚠" * 35)
            print(f"\n  Tool:   {tc['name']}")
            print(f"  Args:   {json.dumps(tc['args'], indent=6)}")

            if tc["name"] == "block_ip_address":
                print(f"\n  🔴 HIGH-RISK: This will BLOCK IP {tc['args'].get('ip_address', '?')}")
                print(f"     Reason: {tc['args'].get('reason', 'N/A')}")
                print(f"     Duration: {tc['args'].get('duration_hours', 24)} hours")

            print("\n" + "─" * 50)
    return last_msg


def run_hitl_demo():
    """Interactive demo showing persistent memory and HITL flow."""
    print("=" * 70)
    print("  Persistent Memory & HITL Agent Demo")
    print("  AI407L Mid-Exam | Ahsan Saleem (2022074)")
    print("=" * 70)

    app, checkpointer = build_hitl_graph()

    # Thread ID for persistent sessions
    thread_id = "security-session-001"
    config = {"configurable": {"thread_id": thread_id}}

    # ── Session 1: Analyze traffic ───────────────────────────────────────
    print("\n📌 SESSION 1: Analyzing traffic (thread: security-session-001)")
    print("─" * 70)

    query1 = "Analyze the network traffic and identify any suspicious IPs that should be blocked."

    print(f"🔍 User: {query1}\n")

    for event in app.stream(
        {"messages": [HumanMessage(content=query1)]},
        config=config,
    ):
        for node_name, node_output in event.items():
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            for tc in msg.tool_calls:
                                print(f"   🛠  Agent wants to call: {tc['name']}")
                        elif msg.content:
                            print(f"   💬 Agent: {msg.content[:400]}")
                    elif isinstance(msg, ToolMessage):
                        print(f"   📊 Tool result: {msg.content[:200]}…")

    # ── Check for interrupt (pending tool call) ──────────────────────────
    current_state = app.get_state(config)
    
    if current_state.next:
        print("\n⏸  Graph paused — pending tool execution requires approval")
        display_pending_action(current_state.values)
        
        # Simulate human approval options
        print("\n  Options:")
        print("    [1] ✅ APPROVE — execute as proposed")
        print("    [2] ✏️  EDIT   — modify the action before executing")
        print("    [3] ❌ REJECT  — cancel this action")

        # For demo, we'll show the APPROVE flow
        choice = "1"  # Simulating human approval
        print(f"\n  👤 Human chose: [{'APPROVE' if choice == '1' else 'EDIT' if choice == '2' else 'REJECT'}]")

        if choice == "1":
            # APPROVE: Resume execution
            print("\n  ✅ Action APPROVED — resuming execution…\n")
            for event in app.stream(None, config=config):
                for node_name, node_output in event.items():
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, AIMessage):
                                if msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        print(f"   🛠  Tool call: {tc['name']}")
                                elif msg.content:
                                    print(f"   💬 Agent: {msg.content[:400]}")
                            elif isinstance(msg, ToolMessage):
                                print(f"   📊 Tool result: {msg.content[:200]}…")

                    # Check for another interrupt
                    new_state = app.get_state(config)
                    if new_state.next:
                        print("\n⏸  Another action pending approval…")
                        display_pending_action(new_state.values)
                        print("\n  👤 Human: APPROVE")
                        # Continue
                        continue

        elif choice == "2":
            # EDIT: Modify the pending action
            print("\n  ✏️  Editing action — changing IP to 10.0.0.99…")
            # Update the tool call by modifying state
            last_msg = current_state.values["messages"][-1]
            if last_msg.tool_calls:
                last_msg.tool_calls[0]["args"]["ip_address"] = "10.0.0.99"
                last_msg.tool_calls[0]["args"]["reason"] = "Edited by human analyst"
            app.update_state(config, {"messages": [last_msg]})
            # Resume
            for event in app.stream(None, config=config):
                pass

        elif choice == "3":
            # REJECT: Cancel by providing a rejection message
            print("\n  ❌ Action REJECTED — providing feedback…")
            reject_msg = ToolMessage(
                content="Action cancelled by human operator. The analyst decided this IP should not be blocked at this time.",
                tool_call_id=current_state.values["messages"][-1].tool_calls[0]["id"],
            )
            app.update_state(config, {"messages": [reject_msg]}, as_node="tools")
            for event in app.stream(None, config=config):
                for node_name, node_output in event.items():
                    if "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, AIMessage) and msg.content:
                                print(f"   💬 Agent: {msg.content[:400]}")

    # Continue processing any remaining interrupts
    while True:
        state = app.get_state(config)
        if not state.next:
            break
        print("\n⏸  Additional action pending…")
        display_pending_action(state.values)
        print("  👤 Human: APPROVE")
        for event in app.stream(None, config=config):
            for node_name, node_output in event.items():
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            print(f"   💬 Agent: {msg.content[:300]}")
                        elif isinstance(msg, ToolMessage):
                            print(f"   📊 Tool: {msg.content[:200]}…")

    # ── Session 2: Demonstrate session recovery ─────────────────────────
    print("\n\n📌 SESSION 2: Recovering previous session (same thread_id)")
    print("─" * 70)

    recovered_state = app.get_state(config)
    msg_count = len(recovered_state.values.get("messages", []))
    print(f"   ✅ Session recovered! Found {msg_count} messages from previous session.")
    print(f"   📝 Thread ID: {thread_id}")

    # Continue the conversation in the same thread
    followup = "What was the summary of the analysis you just performed?"
    print(f"\n🔍 User: {followup}\n")

    for event in app.stream(
        {"messages": [HumanMessage(content=followup)]},
        config=config,
    ):
        for node_name, node_output in event.items():
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if isinstance(msg, AIMessage) and msg.content:
                        print(f"   💬 Agent: {msg.content[:500]}")

    # Handle any remaining interrupts from session 2
    while True:
        state = app.get_state(config)
        if not state.next:
            break
        print("  👤 Human: APPROVE")
        for event in app.stream(None, config=config):
            for node_name, node_output in event.items():
                if "messages" in node_output:
                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage) and msg.content:
                            print(f"   💬 Agent: {msg.content[:300]}")

    print("\n" + "=" * 70)
    print("  HITL demo complete — persistent memory & human approval verified.")
    print("=" * 70)


if __name__ == "__main__":
    run_hitl_demo()
