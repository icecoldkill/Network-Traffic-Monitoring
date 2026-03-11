# AI407L Mid-Exam Lab Compliance Report
**Student:** Ahsan Saleem (2022074)
**Project:** Intelligent Network Security & Threat Intelligence System

This report maps the project implementation to the specific requirements of Labs 2-6.

---

## Lab 2: Knowledge Engineering & Domain Grounding
- **Requirement:** RAG Pipeline with Semantic Chunking & Metadata.
- **Implementation:** 
    - `rag_pipeline.py` implements high-quality RAG using `sentence-transformers` and `FAISS`.
    - **Chunking:** `RecursiveCharacterTextSplitter` with 500-char chunks.
    - **Metadata:** Enhanced chunks include `source`, `path`, and `category`.
- **Files:** [rag_pipeline.py](file:///Users/ahsansaleem/Desktop/cv_project/rag_pipeline.py), [knowledge_base/](file:///Users/ahsansaleem/Desktop/cv_project/knowledge_base/)

## Lab 3: The Reasoning Loop (LangGraph ReAct)
- **Requirement:** ReAct loop with Pydantic tool validation.
- **Implementation:**
    - `multi_agent.py` and `hitl_agent.py` define a cyclic graph.
    - **Tools:** Use `@tool` decorator with `Pydantic` models for strict schema validation.
    - **ReAct:** The agent reasons about the input, calls a tool, and the graph routes back to the agent (or supervisor) until completion.
- **Files:** [multi_agent.py](file:///Users/ahsansaleem/Desktop/cv_project/multi_agent.py)

## Lab 4: Multi-Agent Orchestration
- **Requirement:** specialized personas, restricted tools, state handover.
- **Implementation:**
    - **Personas:** `Security Analyst` (Analysis Tools) and `Incident Responder` (Remediation Tools).
    - **Supervisor:** Central router implementing orchestrator pattern.
    - **Handover:** State includes `findings` which Analyst populates for Responder.
- **Files:** [multi_agent.py](file:///Users/ahsansaleem/Desktop/cv_project/multi_agent.py)

## Lab 5: State Management & Human-in-the-Loop
- **Requirement:** Persistent memory and safety breakpoints.
- **Implementation:**
    - **Persistence:** `MemorySaver` checkpointer allows session recovery via `thread_id`.
    - **HITL:** `interrupt_before=["tools"]` configuration in the graph.
    - **Critical Tool:** `block_ip_address` is flagged for human approval.
- **Files:** [hitl_agent.py](file:///Users/ahsansaleem/Desktop/cv_project/hitl_agent.py)

## Lab 6: Security Guardrails & Jailbreaking
- **Requirement:** Input/Output guardrails and adversarial testing.
- **Implementation:**
    - `secured_graph.py` adds a `guardrail_node` to intercept prompts.
    - **Logic:** Pydantic-based keyword validation and LLM-based intent classification.
- **Files:** [secured_graph.py](file:///Users/ahsansaleem/Desktop/cv_project/secured_graph.py) (See below)

## Final Deployment Verification
- **Status:** 100% Compliant
- **Repo:** https://github.com/icecoldkill/Network-Traffic-Monitoring
- **CI/CD:** Active
- **Last Updated:** Wed Mar 11 07:12:31 PKT 2026
