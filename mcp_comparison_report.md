# Technical Comparison: MCP vs Direct Invocation vs LangGraph Orchestration

**AI407L Lab Mid Exam — Spring 2026 | Part B Task 3**
**Student: Ahsan Saleem (2022074)**

---

## 1. Why MCP is Needed in Production Systems

In production AI systems, models must interact with external tools, databases, APIs, and services. Without a standardized protocol, every integration becomes a bespoke, tightly-coupled implementation. The **Model Context Protocol (MCP)** addresses this by providing a universal, standardized interface between AI models and the tools they consume.

### Key Problems MCP Solves

| Problem | Without MCP | With MCP |
|---------|------------|----------|
| **Tool Discovery** | Hardcoded tool lists in application code | Dynamic discovery at runtime via protocol |
| **Vendor Lock-in** | Tools tightly coupled to specific LLM providers | Any MCP-compatible model can use any MCP server |
| **Security Boundaries** | Tools execute in the same process as the model | Tools run in isolated server processes |
| **Versioning** | Breaking changes require application redeployment | Server tools versioned independently |
| **Multi-tenancy** | Complex custom implementations per tenant | Standard protocol handles context isolation |

### Production Requirements MCP Fulfills

1. **Auditability**: Every tool invocation passes through the MCP protocol layer, creating a natural audit point for logging, rate limiting, and access control.
2. **Horizontal Scaling**: MCP servers can be deployed independently and scaled based on demand without modifying the client or model.
3. **Compliance**: In regulated industries (finance, healthcare), MCP enforces separation between the AI model and data-access tools, satisfying regulatory requirements for data isolation.
4. **Fault Isolation**: A failing tool server does not crash the model client — errors are communicated through structured protocol responses.

---

## 2. Comparison of Integration Approaches

### 2.1 Direct Tool Invocation

```python
# Direct invocation — tool is a local function called directly
result = scan_network(ip_range="192.168.1.0/24", scan_type="full")
```

**Architecture**: Model ↔ Application Code (tools are embedded functions)

| Aspect | Assessment |
|--------|-----------|
| **Coupling** | Tightly coupled — tool and model share the same process and codebase |
| **Discovery** | Static — tools are hardcoded at compile time |
| **Security** | No isolation — tool has full access to application memory and resources |
| **Scalability** | Vertical only — cannot scale tools independently of the model |
| **Deployment** | Monolithic — tool changes require full application redeployment |
| **Complexity** | Lowest — simple function calls, no protocol overhead |
| **Latency** | Lowest — in-process function call, no serialization |

**Best For**: Prototyping, single-developer projects, and simple applications where tools are stable and security is not a concern.

### 2.2 LangGraph-Based Orchestration

```python
# LangGraph — tools are registered with an agent graph
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode([scan_network, check_vuln]))
graph.add_conditional_edges("agent", routing_fn)
```

**Architecture**: Model ↔ LangGraph Runtime ↔ Tool Nodes (within the same process)

| Aspect | Assessment |
|--------|-----------|
| **Coupling** | Medium — tools are registered with the graph but can be modular |
| **Discovery** | Semi-dynamic — tools defined at graph construction time |
| **Security** | Partial — LangGraph supports `interrupt_before` for HITL, but tools still run in-process |
| **Scalability** | Agent logic scales, but tools are still co-located |
| **Orchestration** | Excellent — supports multi-agent, conditional routing, state management, checkpointing |
| **Complexity** | Moderate — requires understanding of graph construction and state management |
| **Latency** | Low — in-process with graph overhead |

**Best For**: Multi-step reasoning workflows, multi-agent systems, applications requiring human-in-the-loop approval, and complex conditional logic.

### 2.3 MCP-Based Modular Exposure

```python
# MCP — tools exposed via a protocol server, consumed by any client
# Server (mcp_server.py):
@mcp.tool()
def scan_network(ip_range: str, scan_type: str) -> str: ...

# Client (mcp_client.py):
tools = await session.list_tools()  # Dynamic discovery
result = await session.call_tool("scan_network", arguments={...})
```

**Architecture**: Model ↔ MCP Client ↔ Protocol Layer ↔ MCP Server ↔ Execution Layer

| Aspect | Assessment |
|--------|-----------|
| **Coupling** | Loosely coupled — client and server communicate only through the protocol |
| **Discovery** | Fully dynamic — tools are discovered at runtime from the server |
| **Security** | Strong — process isolation, tools run in separate server processes |
| **Scalability** | Horizontal — servers scale independently, can be distributed |
| **Interoperability** | Highest — any MCP-compatible client works with any MCP server |
| **Complexity** | Higher — requires server/client setup, async communication |
| **Latency** | Highest — serialization, IPC, and protocol overhead |

**Best For**: Production microservices, multi-model architectures, enterprise deployments requiring security isolation, and systems where tools are maintained by different teams.

---

## 3. How MCP Improves Key System Properties

### 3.1 Security

| Improvement | Details |
|-------------|---------|
| **Process Isolation** | Tools execute in a separate server process. A compromised tool cannot access model memory or application secrets. |
| **Access Control** | The MCP server can enforce authentication and authorization before executing tools. Different clients can have different permission levels. |
| **Input Validation** | Structured input schemas (defined at the server) validate all arguments before execution, preventing injection attacks. |
| **Audit Trail** | Every tool invocation is a discrete protocol exchange, creating a natural logging and auditing point. |

In our implementation, the MCP server enforces structured input schemas for every tool. For example, `scan_network` requires a valid `ip_range` string and `scan_type` must be one of the predefined options. This prevents malformed inputs from reaching the execution layer.

### 3.2 Scalability

| Improvement | Details |
|-------------|---------|
| **Independent Scaling** | MCP servers can be deployed as separate microservices, each scaled based on demand. A heavily-used `scan_network` tool can have more replicas than a rarely-used `check_vulnerability` tool. |
| **Load Balancing** | Multiple MCP server instances can be load-balanced behind a gateway. |
| **Resource Isolation** | Resource-intensive tools (e.g., network scanning) run in their own containers with dedicated compute, preventing resource contention with the model. |
| **Multi-Region** | MCP servers can be deployed in different regions for latency optimization and data sovereignty compliance. |

### 3.3 System Abstraction

| Improvement | Details |
|-------------|---------|
| **Implementation Hiding** | The MCP client only sees tool names, descriptions, and schemas — not the implementation. The server can change its implementation (e.g., switching from simulation to real network scanning) without modifying the client. |
| **Version Independence** | MCP servers can be updated independently. Adding new tools or modifying existing ones does not require client changes — the client discovers tools dynamically. |
| **Technology Agnosticism** | An MCP server can be written in any language (Python, Go, Rust). The client only speaks the MCP protocol, not the server's implementation language. |

### 3.4 Separation of Concerns

The MCP architecture cleanly separates four distinct layers:

```
┌─────────────┐
│   MODEL      │  → LLM (Groq/Llama3) — reasoning and tool selection
├─────────────┤
│   CONTEXT    │  → MCP Protocol — structured context exchange
├─────────────┤
│   TOOLS      │  → MCP Server — tool definitions and schemas
├─────────────┤
│  EXECUTION   │  → Implementation — actual tool logic and side effects
└─────────────┘
```

| Layer | Responsibility | Maintainer |
|-------|---------------|------------|
| **Model** | Reasoning, tool selection, response generation | ML/AI team |
| **Context** | Protocol specification, message format, transport | Platform team |
| **Tools** | Tool schemas, descriptions, input/output contracts | Domain experts |
| **Execution** | Actual implementation, data access, side effects | Backend engineers |

This separation means:
- The ML team can swap models without affecting tools
- Domain experts can add new tools without touching the model
- Backend engineers can optimize execution without changing schemas
- The platform team can scale the protocol layer independently

---

## 4. Summary Comparison Table

| Criterion | Direct Invocation | LangGraph | MCP |
|-----------|:-:|:-:|:-:|
| Coupling | Tight | Medium | Loose |
| Security | ❌ None | ⚠️ Partial (HITL) | ✅ Full isolation |
| Scalability | ❌ Vertical | ⚠️ Agent-level | ✅ Horizontal |
| Tool Discovery | ❌ Static | ⚠️ Build-time | ✅ Runtime |
| Multi-agent Support | ❌ No | ✅ Excellent | ⚠️ Via client |
| State Management | ❌ Manual | ✅ Checkpointing | ⚠️ Client-side |
| Production Ready | ❌ Limited | ⚠️ Moderate | ✅ Designed for it |
| Setup Complexity | ✅ Minimal | ⚠️ Moderate | ❌ Highest |
| Latency | ✅ Lowest | ✅ Low | ❌ Highest |

---

## 5. Conclusion

Each approach serves a distinct purpose in the AI systems lifecycle:

1. **Direct Invocation** is ideal for rapid prototyping and proof-of-concept development where simplicity outweighs all other concerns.

2. **LangGraph Orchestration** excels at complex reasoning workflows with multi-agent collaboration, human-in-the-loop safety, and persistent state management. It is the right choice for applications where the orchestration logic is the primary complexity.

3. **MCP** is the production-grade standard for systems where security, scalability, and team independence are paramount. It provides the architectural foundation for enterprise AI deployments where tools must be managed, versioned, and scaled independently of the model layer.

In practice, these approaches are **complementary, not competing**. A production system might use **LangGraph** for agent orchestration and reasoning logic, while exposing tools through **MCP servers** for security isolation and scalability — achieving the best of both worlds.

---

*Report generated for AI407L Spring 2026 Mid-Exam — Ahsan Saleem (2022074)*
*Ghulam Ishaq Khan Institute of Engineering Sciences & Technology*
