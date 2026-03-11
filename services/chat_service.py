import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatService:
    def __init__(self, api_key: str = None):
        self.groq_api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable or pass api_key parameter.")
            
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
    async def get_network_status(self) -> Dict[str, Any]:
        """Get current network status summary"""
        # This is a placeholder - implement actual network status check
        return {
            "status": "operational",
            "active_connections": 42,
            "anomalies_detected": 3,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def get_anomaly_report(self) -> Dict[str, Any]:
        """Get latest anomaly report"""
        # This is a placeholder - implement actual anomaly report
        return {
            "total_anomalies": 5,
            "critical": 1,
            "high": 2,
            "medium": 1,
            "low": 1,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def block_ip(self, ip_address: str, reason: str) -> Dict[str, Any]:
        """Block an IP address"""
        # This is a placeholder - implement actual IP blocking
        return {
            "status": "success",
            "action": "block_ip",
            "ip_address": ip_address,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_traffic(self, timeframe: str = "1h") -> Dict[str, Any]:
        """Analyze network traffic for a given timeframe"""
        # This is a placeholder - implement actual traffic analysis
        return {
            "timeframe": timeframe,
            "total_packets": 1500000,
            "average_throughput": "1.2 Gbps",
            "top_source_ips": ["192.168.1.1", "10.0.0.5", "172.16.0.3"],
            "top_destinations": ["example.com", "api.service.com", "cdn.provider.net"],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def process_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process chat messages using Groq API"""
        if not self.groq_api_key:
            return {
                "error": "Groq API key not configured",
                "status": "error"
            }
        
        try:
            # Define available tools/functions the LLM can call
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "get_network_status",
                        "description": "Get the current status of the network",
                        "parameters": {"type": "object", "properties": {}}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_anomaly_report",
                        "description": "Get the latest anomaly detection report",
                        "parameters": {"type": "object", "properties": {}}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "block_ip",
                        "description": "Block a specific IP address",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "ip_address": {"type": "string", "description": "IP address to block"},
                                "reason": {"type": "string", "description": "Reason for blocking"}
                            },
                            "required": ["ip_address", "reason"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_traffic",
                        "description": "Analyze network traffic patterns",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "timeframe": {
                                    "type": "string",
                                    "enum": ["5m", "15m", "1h", "6h", "24h"],
                                    "description": "Time window for analysis"
                                }
                            },
                            "required": ["timeframe"]
                        }
                    }
                }
            ]
            
            # Prepare the request to Groq API
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto"
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Check if the model wants to call a function
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if choice["finish_reason"] == "tool_calls":
                    # Handle function calls
                    tool_calls = choice["message"].get("tool_calls", [])
                    
                    # Process each tool call
                    for tool_call in tool_calls:
                        function_name = tool_call["function"]["name"]
                        function_args = json.loads(tool_call["function"]["arguments"])
                        
                        # Call the appropriate function
                        if function_name == "get_network_status":
                            result = await self.get_network_status()
                        elif function_name == "get_anomaly_report":
                            result = await self.get_anomaly_report()
                        elif function_name == "block_ip":
                            result = await self.block_ip(
                                ip_address=function_args["ip_address"],
                                reason=function_args["reason"]
                            )
                        elif function_name == "analyze_traffic":
                            result = await self.analyze_traffic(
                                timeframe=function_args.get("timeframe", "1h")
                            )
                        else:
                            result = {"error": f"Unknown function: {function_name}"}
                        
                        # Add the function call result to the messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": function_name,
                            "content": json.dumps(result)
                        })
                    
                    # Get a new completion with the function call results
                    return await self.process_chat(messages)
                
                # Return the final response
                return {
                    "response": choice["message"]["content"],
                    "status": "success"
                }
            
            return {
                "error": "No response from Groq API",
                "status": "error"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
