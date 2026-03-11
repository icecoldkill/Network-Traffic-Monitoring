# PRD.md: Product Requirements Document

## 1. Problem Statement
Security Operations Centers (SOCs) are overwhelmed by high-volume network traffic and a barrage of security alerts. Manual analysis is slow, error-prone, and cannot scale with modern network speeds. This leads to delayed response times (MTTR) and increased risk of data breaches. 

The **Intelligent Network Security & Threat Intelligence System** solves this bottleneck by providing an autonomous multi-agent pipeline that can:
- Capture and analyze traffic in real-time.
- Ground AI reasoning in specific domain knowledge (RAG).
- Orchestrate specialized agents for detection and response.
- Maintain human oversight (HITL) for high-risk actions.

## 2. User Personas
- **Tier 1 Security Analyst:** Primary user who monitors the dashboard and approves/rejects automated response actions.
- **SOC Manager:** Reviews the generated incident reports and high-level traffic summaries.
- **Network Engineer:** Uses the system to troubleshoot specific traffic anomalies.

## 3. Success Metrics
- **Mean Time to Detect (MTTD):** Under 30 seconds for known anomaly patterns.
- **Mean Time to Respond (MTTR):** Reduction of response time by 60% compared to manual IP blocking.
- **Accuracy:** Over 90% F1-score on standard intrusion detection datasets (e.g., CIC-IDS2018).
- **False Positive Rate:** Under 5% for automated blocking suggestions.

## 4. System Architecture
The system utilizes a **LangGraph-driven Multi-Agent architecture**:
1. **Supervisor:** Orchestrates the flow.
2. **Analyst:** Handles data crunching and RAG retrieval.
3. **Responder:** Generates remediations and handles HITL.
