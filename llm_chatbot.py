import os
import json
import requests
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqChatbot:
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Groq chatbot.
        
        Args:
            api_key: Your Groq API key. If not provided, will look for GROQ_API_KEY environment variable.
            model: The model to use for chat completions. Default is "llama-3.3-70b-versatile".
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided. Set GROQ_API_KEY environment variable or pass api_key parameter.")
            
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # System prompt for security operations
        self.system_prompt = """You are a security operations assistant. Your role is to help analyze network traffic, 
        detect anomalies, and suggest security actions. Be concise and technical in your responses. 
        When asked about security incidents or threats, provide actionable recommendations."""
        
    def _make_api_call(self, messages: List[Dict[str, str]]) -> Dict:
        """Make an API call to Groq's chat completion endpoint."""
        try:
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise
    
    def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Send a message to the chatbot and get a response.
        
        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages in the conversation
            
        Returns:
            Dict containing the response and updated conversation history
        """
        if conversation_history is None:
            conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": user_message})
        
        try:
            # Make the API call
            response = self._make_api_call(conversation_history)
            
            # Extract the assistant's response
            assistant_message = response['choices'][0]['message']['content']
            
            # Add assistant's response to history
            conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return {
                "response": assistant_message,
                "conversation_history": conversation_history
            }
            
        except Exception as e:
            error_msg = f"Error in chat: {str(e)}"
            logger.error(error_msg)
            return {
                "response": "I'm sorry, I encountered an error processing your request. Please try again.",
                "error": error_msg,
                "conversation_history": conversation_history
            }
    
    def analyze_anomaly(self, anomaly_data: Dict) -> Dict:
        """
        Analyze network anomaly data and provide security recommendations.
        
        Args:
            anomaly_data: Dictionary containing anomaly details
            
        Returns:
            Dict containing analysis and recommendations
        """
        prompt = f"""Analyze the following network anomaly and provide security recommendations:
        
        Anomaly Details:
        {json.dumps(anomaly_data, indent=2)}
        
        Please provide:
        1. A brief analysis of the anomaly
        2. Potential security implications
        3. Recommended actions to mitigate the threat
        4. Any additional context or references
        """
        
        return self.chat(prompt)

# Example usage
if __name__ == "__main__":
    # Initialize with your API key
    chatbot = GroqChatbot(api_key=os.getenv("GROQ_API_KEY"))
    
    # Example chat
    response = chatbot.chat("What are some common network security threats?")
    print("Assistant:", response['response'])
    
    # Example anomaly analysis
    anomaly_data = {
        "timestamp": "2023-11-12T01:23:45Z",
        "source_ip": "192.168.1.100",
        "destination_ip": "10.0.0.1",
        "protocol": "TCP",
        "port": 22,
        "severity": "high",
        "description": "Multiple failed SSH login attempts detected"
    }
    
    analysis = chatbot.analyze_anomaly(anomaly_data)
    print("\nAnomaly Analysis:", analysis['response'])
