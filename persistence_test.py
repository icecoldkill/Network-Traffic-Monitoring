# persistence_test.py
import time
from hitl_agent import build_hitl_graph
from langchain_core.messages import HumanMessage

def test_session_recovery():
    print("=" * 70)
    print("  Lab 5: Persistent Memory Test  ")
    print("=" * 70)
    
    app, _ = build_hitl_graph()
    thread_id = "test-session-123"
    config = {"configurable": {"thread_id": thread_id}}
    
    # 1. Start session
    print(f"\n[1] Starting session with thread: {thread_id}")
    msg1 = "Hello, my name is Ahsan and I am a Tier 1 Analyst."
    print(f"    User: {msg1}")
    for event in app.stream({"messages": [HumanMessage(content=msg1)]}, config=config):
        pass
    
    print("\n[2] Script 'stopped'... (simulating restart)")
    time.sleep(1)
    
    # 2. Recover session
    print(f"\n[3] Restarting session with SAME thread: {thread_id}")
    msg2 = "What is my name and role?"
    print(f"    User: {msg2}")
    
    found_name = False
    for event in app.stream({"messages": [HumanMessage(content=msg2)]}, config=config):
        for node_name, output in event.items():
            if "messages" in output:
                res = output["messages"][-1].content
                print(f"    Agent: {res}")
                if "Ahsan" in res:
                    found_name = True
    
    if found_name:
        print("\n✅ SUCCESS: Agent remembered context across 'restarts'!")
    else:
        print("\n❌ FAILURE: Agent forgot context.")

if __name__ == "__main__":
    test_session_recovery()
