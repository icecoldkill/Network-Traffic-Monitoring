# approval_logic.py
# HITL approval configuration for Lab 5
from hitl_agent import build_hitl_graph

# The graph is compiled with interrupt_before=["tools"]
app, checkpointer = build_hitl_graph()

print("✅ HITL Approval Logic enabled: interrupt_before=['tools'] ensures safety pause for sensitive actions.")
