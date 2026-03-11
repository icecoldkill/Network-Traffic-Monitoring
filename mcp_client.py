# mcp_client.py
"""
Model Context Protocol (MCP) Client — Network Security
AI407L Lab Mid Exam - Spring 2026 | Part B Task 2
Student: Ahsan Saleem (2022074)

MCP client that:
1. Connects to the MCP server (mcp_server.py) via stdio transport
2. Discovers available tools from the server
3. Integrates with Groq LLM for intelligent tool selection
4. Executes tools via MCP protocol (NOT direct function calls)
5. Captures and displays structured responses
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_groq import ChatGroq
import weave
from weave.integrations.langchain import WeaveTracer

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"


class MCPSecurityClient:
    """
    MCP client that connects to the Network Security MCP server,
    discovers tools, and uses Groq LLM to intelligently invoke them.
    """

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not set")

        self.llm = ChatGroq(
            model=GROQ_MODEL,
            api_key=self.groq_api_key,
            temperature=0.2,
            callbacks=[WeaveTracer()]
        )
        self.session = None
        self.available_tools: List[Dict] = []

    async def connect_to_server(self):
        """Establish connection to MCP server via stdio transport."""
        server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")

        server_params = StdioServerParameters(
            command=sys.executable,  # current Python interpreter
            args=[server_path],
            env=None,
        )

        # Start stdio connection
        self._stdio_cm = stdio_client(server_params)
        streams = await self._stdio_cm.__aenter__()
        read_stream, write_stream = streams

        self._session_cm = ClientSession(read_stream, write_stream)
        self.session = await self._session_cm.__aenter__()

        # Initialize the MCP session
        await self.session.initialize()
        print("✅ Connected to MCP server")

    async def disconnect(self):
        """Clean up MCP session."""
        if self._session_cm:
            await self._session_cm.__aexit__(None, None, None)
        if self._stdio_cm:
            await self._stdio_cm.__aexit__(None, None, None)
        print("🔌 Disconnected from MCP server")

    @weave.op()
    async def discover_tools(self) -> List[Dict]:
        """Discover available tools from the MCP server."""
        response = await self.session.list_tools()
        self.available_tools = []

        for tool in response.tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            self.available_tools.append(tool_info)

        return self.available_tools

    @weave.op()
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool on the MCP server via the protocol."""
        result = await self.session.call_tool(tool_name, arguments=arguments)

        # Extract text content from result
        if result.content:
            return "\n".join(
                block.text for block in result.content if hasattr(block, "text")
            )
        return "No output returned"

    @weave.op()
    async def process_query(self, user_query: str) -> str:
        """
        Process user query end-to-end:
        1. Ask LLM which tool to use (with tool schemas as context)
        2. Execute the selected tool via MCP
        3. Send results back to LLM for final answer
        """
        # Build tool descriptions for the LLM
        tools_desc = json.dumps(self.available_tools, indent=2)

        # Step 1: Ask LLM to decide which tool to call
        planning_prompt = f"""You are a network security assistant. You have access to the following tools via MCP:

{tools_desc}

Based on the user query, decide which tool to call and provide the arguments.
Respond with ONLY a JSON object like:
{{"tool": "tool_name", "arguments": {{"arg1": "value1"}}}}

User Query: {user_query}"""

        plan_response = self.llm.invoke(planning_prompt)
        plan_text = plan_response.content.strip()

        # Parse the LLM's tool selection
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```" in plan_text:
                plan_text = plan_text.split("```")[1]
                if plan_text.startswith("json"):
                    plan_text = plan_text[4:]
            tool_plan = json.loads(plan_text.strip())
        except json.JSONDecodeError:
            return f"LLM could not determine tool to use. Raw response: {plan_text}"

        tool_name = tool_plan.get("tool", "")
        arguments = tool_plan.get("arguments", {})

        print(f"   🧠 LLM selected tool: {tool_name}")
        print(f"   📋 Arguments: {json.dumps(arguments, indent=4)}")

        # Step 2: Execute the tool via MCP protocol
        print(f"\n   🔧 Executing {tool_name} via MCP protocol…")
        tool_result = await self.execute_tool(tool_name, arguments)

        print(f"   📊 Tool returned {len(tool_result)} chars of data")

        # Step 3: Send tool results to LLM for final interpretation
        interpretation_prompt = f"""You are a network security expert. A tool was executed via MCP with these results:

Tool: {tool_name}
Arguments: {json.dumps(arguments)}
Result:
{tool_result}

Original User Query: {user_query}

Provide a clear, professional analysis of the results. Highlight any security concerns and recommendations."""

        final_response = self.llm.invoke(interpretation_prompt)
        return final_response.content


async def run_demo():
    """Full MCP client demo with tool discovery, invocation, and response handling."""
    print("=" * 70)
    print("  MCP Client — Network Security Pipeline")
    print("  AI407L Mid-Exam | Ahsan Saleem (2022074)")
    print("=" * 70)
    
    # Initialize W&B Weave for LLM observability
    weave.init("network-anomaly-detection-mcp")

    client = MCPSecurityClient()

    try:
        # ── Step 1: Connect ──────────────────────────────────────────────
        print("\n📡 Step 1: Connecting to MCP server…")
        await client.connect_to_server()

        # ── Step 2: Tool Discovery ───────────────────────────────────────
        print("\n🔍 Step 2: Discovering available tools…")
        tools = await client.discover_tools()
        print(f"\n   Found {len(tools)} tools:")
        for t in tools:
            print(f"   • {t['name']}: {t['description'][:80]}")

        # ── Step 3: Execute tools via MCP ────────────────────────────────
        demo_queries = [
            "Scan the network 192.168.1.0/24 and report what hosts are active",
            "Check if CVE-2014-0160 (Heartbleed) is a known vulnerability and what its severity is",
            "Get threat intelligence on IP address 45.33.32.156",
        ]

        for i, query in enumerate(demo_queries, 1):
            print(f"\n{'─' * 70}")
            print(f"📝 Query {i}: {query}")
            print("─" * 70)

            result = await client.process_query(query)
            print(f"\n💬 Analysis:\n{result[:600]}")

    finally:
        # ── Disconnect ───────────────────────────────────────────────────
        print(f"\n{'─' * 70}")
        await client.disconnect()

    print("\n" + "=" * 70)
    print("  MCP pipeline demo complete.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
