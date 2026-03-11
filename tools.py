# tools.py
# Extracting tools from multi_agent.py for Lab 3 compliance
from multi_agent import (
    analyst_analyze_traffic, analyst_detect_anomalies, analyst_query_kb,
    responder_generate_report, responder_block_ip, responder_recommend_action
)

# Mandatory Task 1 Lab 3: Every tool uses @tool and Pydantic validation
# These are exported from multi_agent.py which already implements these requirements.
print("✅ Tools imported from multi_agent.py with Pydantic validation.")
