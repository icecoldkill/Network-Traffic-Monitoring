# Part B: Standalone MCP Pipeline - Compliance Report
**Student:** Ahsan Saleem (2022074)
**Project:** Model Context Protocol (MCP) for Network Security

This report details the implementation of the standalone MCP pipeline, fulfilling the requirements of Part B of the AI407L Spring 2026 Mid-Exam.

---

## 1. Task 1: Standalone MCP Server
The MCP server is implemented in `mcp_server.py` as a completely independent process, separated from the Part A LangGraph system.

### Key Implementation Details:
- **Framework:** Built using the `FastMCP` framework for high-level tool definition.
- **Protocol:** Uses the official Model Context Protocol (MCP) over `stdio` transport.
- **Tools Exposed:**
    1. `scan_network`: Accepts `ip_range` and `scan_type`. Returns a structured JSON result of simulated active hosts and open ports.
    2. `check_vulnerability`: Accepts a `cve_id`. Returns detailed CVSS scores, descriptions, and remediations.
    3. `get_threat_intel`: Accepts an `indicator` (IP/Domain). Returns risk scores and associated threat actors.
- **Separation of Concerns:** 
    - **Model:** Independent LLM client (Groq).
    - **Context:** Managed via the MCP protocol session.
    - **Tools:** Defined via `@mcp.tool()` decorators with strict Pydantic-style argument types.
    - **Execution:** Isolated logic within tool functions.

**File:** [mcp_server.py](file:///Users/ahsansaleem/Desktop/cv_project/mcp_server.py)

---

## 2. Task 2: MCP Client-Side Interaction
The client-side pipeline is implemented in `mcp_client.py`, demonstrating the end-to-end tool discovery and execution flow.

### Workflow:
1. **Connection:** Establishes a `StdioServerParameters` connection to launch the Python server process.
2. **Discovery:** Dynamically calls `session.list_tools()` to retrieve available capabilities without prior hardcoding.
3. **Reasoning:** Uses `llama-3.3-70b-versatile` to analyze the user query and select the appropriate tool from the discovered list.
4. **Invocation:** Executes the tool via `session.call_tool()`, passing structured arguments as JSON.
5. **Response Handling:** Captures the JSON output from the server, parses it, and feeds it back to the LLM for a final human-readable interpretation.

**File:** [mcp_client.py](file:///Users/ahsansaleem/Desktop/cv_project/mcp_client.py)

---

## 3. Task 3: Technical Comparison & Justification
A formal technical document has been authored to justify the use of MCP in production environments.

### Core Arguments:
- **Security:** MCP provides process-level isolation. Tools run in their own environment, protecting the model's memory space.
- **Scalability:** Unlike direct function calls, MCP servers can be scaled horizontally or deployed as microservices.
- **System Abstraction:** Models only need to know the protocol, not the underlying tool implementation (Python, Go, Rust, etc.).
- **Modularity:** MCP allows the "Action" layer to be developed and versioned independently from the "Reasoning" layer.

**File:** [mcp_comparison_report.md](file:///Users/ahsansaleem/Desktop/cv_project/mcp_comparison_report.md)

---

## 4. How to Run & Verify
### Start the Pipeline:
```bash
python mcp_client.py
```
This script will:
1. Spin up the `mcp_server.py` in the background.
2. List all discovered tools.
3. Send a series of test queries (Scan, CVE Check, Threat Intel).
4. Display the traces (observable via W&B Weave).
