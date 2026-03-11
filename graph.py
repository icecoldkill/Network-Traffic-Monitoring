# graph.py
# Compiled LangGraph for Lab 3 compliance
from multi_agent import build_multi_agent_graph

# Build the compiled graph state
app = build_multi_agent_graph()

print("✅ Compiled LangGraph with ReAct loop (Reason + Act) ready for execution.")
if __name__ == "__main__":
    print(app.get_graph().draw_ascii())
