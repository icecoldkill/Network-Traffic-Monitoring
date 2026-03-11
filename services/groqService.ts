import { networkService, type NetworkStatus } from './networkService';

interface GroqMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface GroqResponse {
  response: string;
  conversation_history: GroqMessage[];
  error?: string;
}

export class GroqService {
  private apiKey: string;
  private baseUrl = 'https://api.groq.com/openai/v1/chat/completions';
  private systemPrompt = `You are a security operations assistant. Your role is to help analyze network traffic, 
detect anomalies, and suggest security actions. Be concise and technical in your responses.

You have the following capabilities:
1. View and manage blocked IPs
2. Check network status and active connections
3. Detect and mitigate security threats
4. Analyze network anomalies
5. Provide security recommendations

When responding:
1. Always provide clear, actionable recommendations
2. Use markdown formatting for better readability
3. Include relevant security context when discussing threats
4. When asked about system status, check the current state before responding
5. For security actions, provide step-by-step instructions
6. If you need more information, ask specific questions to clarify`;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  private async handleSecurityCommand(message: string): Promise<string | null> {
    const lowerMessage = message.toLowerCase().trim();
    
    // Check for network status command
    if (lowerMessage.includes('network status') || lowerMessage.includes('status of the network')) {
      const status: NetworkStatus = await networkService.getNetworkStatus();
      return `## Network Status
- Status: ${status.status.toUpperCase()}
- Active Connections: ${status.activeConnections}
- Blocked IPs: ${status.blockedIPs.length}
- Active Threats: ${status.threats.length}

Type 'show threats' to view active threats or 'show blocked' to see blocked IPs.`;
    }
    
    // Check for block IP command
    const blockMatch = lowerMessage.match(/block (?:IP )?(?:address )?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/i);
    if (blockMatch) {
      const ip = blockMatch[1];
      const result = await networkService.blockIP(ip);
      return result.success 
        ? `✅ Successfully blocked IP: ${ip}`
        : `❌ Failed to block IP: ${result.message}`;
    }
    
    // Check for unblock IP command
    const unblockMatch = lowerMessage.match(/unblock (?:IP )?(?:address )?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/i);
    if (unblockMatch) {
      const ip = unblockMatch[1];
      const result = await networkService.unblockIP(ip);
      return result.success 
        ? `✅ Successfully unblocked IP: ${ip}`
        : `❌ Failed to unblock IP: ${result.message}`;
    }
    
    // Check for show blocked IPs
    if (lowerMessage.includes('show blocked') || lowerMessage.includes('list blocked')) {
      const blockedIPs = await networkService.getBlockedIPs();
      return blockedIPs.length > 0
        ? `## Blocked IP Addresses\n${blockedIPs.map(ip => `- ${ip}`).join('\n')}`
        : 'No IP addresses are currently blocked.';
    }
    
    // Check for show threats
    if (lowerMessage.includes('show threats') || lowerMessage.includes('list threats')) {
      const threats = await networkService.getActiveThreats();
      if (threats.length === 0) {
        return 'No active threats detected.';
      }
      
      return `## Active Threats (${threats.length})\n${threats.map(threat => 
        `### ${threat.type.toUpperCase()} - ${threat.severity.toUpperCase()}\n` +
        `- Source: ${threat.sourceIP}\n` +
        `- Description: ${threat.description}\n` +
        `- Detected: ${new Date(threat.timestamp).toLocaleString()}\n` +
        `- Status: ${threat.status}\n` +
        `- Action: Type 'mitigate ${threat.id}' to block this threat\n`
      ).join('\n')}`;
    }
    
    // Check for mitigate threat
    const mitigateMatch = lowerMessage.match(/mitigate (threat-[a-z0-9-]+)/i);
    if (mitigateMatch) {
      const threatId = mitigateMatch[1];
      const result = await networkService.mitigateThreat(threatId);
      return result.success 
        ? `✅ ${result.message}`
        : `❌ Failed to mitigate threat: ${result.message}`;
    }
    
    return null;
  }

  async chat(
    message: string,
    conversationHistory: GroqMessage[] = []
  ): Promise<GroqResponse> {
    try {
      // First check for security commands
      const commandResponse = await this.handleSecurityCommand(message);
      if (commandResponse) {
        return {
          response: commandResponse,
          conversation_history: [
            ...conversationHistory,
            { role: 'user', content: message },
            { role: 'assistant', content: commandResponse }
          ]
        };
      }

      if (!this.apiKey) {
        throw new Error('API key not configured');
      }

      // Initialize messages array with system prompt
      const messages = [
        { role: 'system' as const, content: this.systemPrompt },
        ...conversationHistory,
        { role: 'user' as const, content: message }
      ];

      const requestBody = {
        model: 'mixtral-8x7b-32768',
        messages,
        temperature: 0.7,
        max_tokens: 1000,
        stream: false
      };

      console.log('Sending request to Groq API with messages:', JSON.stringify({
        model: 'mixtral-8x7b-32768',
        messages,
        temperature: 0.7,
        max_tokens: 1000
      }, null, 2));

      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        let errorMessage = `API request failed with status ${response.status}`;
        const errorData = await response.json().catch(() => ({}));
        
        if (response.status === 401) {
          errorMessage = 'Authentication failed. Please check your Groq API key.';
        } else if (response.status === 400) {
          errorMessage = 'Invalid request. Please check your input.';
        } else if (response.status === 429) {
          errorMessage = 'Rate limit exceeded. Please try again later.';
        }
        
        console.error('❌ API Error:', {
          status: response.status,
          statusText: response.statusText,
          message: errorMessage,
          details: errorData
        });
        
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('API Response:', JSON.stringify(data, null, 2));
      
      if (!data.choices?.[0]?.message?.content) {
        throw new Error('Invalid response format from Groq API');
      }

      const assistantMessage = data.choices[0].message.content;
      
      // Update conversation history with both user and assistant messages
      const updatedHistory = [
        ...conversationHistory,
        { role: 'user' as const, content: message },
        { role: 'assistant' as const, content: assistantMessage }
      ];

      return {
        response: assistantMessage,
        conversation_history: updatedHistory
      };
    } catch (error) {
      console.error('Error in GroqService.chat, falling back to string matching:', error);
      
      // Generate a fallback response
      const fallbackResponse = getFallbackResponse(message);
      
      // Update conversation history with both user and assistant messages
      const updatedHistory = [
        ...conversationHistory,
        { role: 'user' as const, content: message },
        { role: 'assistant' as const, content: fallbackResponse }
      ];

      return {
        response: fallbackResponse,
        conversation_history: updatedHistory
      };
    }
  }

  async analyzeAnomaly(anomalyData: any): Promise<GroqResponse> {
    const prompt = `Analyze the following network anomaly and provide security recommendations:
    
Anomaly Details:
${JSON.stringify(anomalyData, null, 2)}

Please provide:
1. A brief analysis of the anomaly
2. Potential security implications
3. Recommended actions to mitigate the threat
4. Any additional context or references`;

    return this.chat(prompt);
  }
}

// Simple response patterns for fallback
const FALLBACK_RESPONSES: {pattern: RegExp, response: string | ((message: string) => Promise<string>)}[] = [
  { 
    pattern: /hello|hi|hey/i, 
    response: 'Hello! I\'m your Security Operations Assistant. I can help you with network monitoring, threat detection, and security management. How can I assist you today?' 
  },
  { 
    pattern: /network status|check network|network health/i, 
    response: async () => {
      const status = await networkService.getNetworkStatus();
      return `## Network Status
- Status: ${status.status.toUpperCase()}
- Active Connections: ${status.activeConnections}
- Blocked IPs: ${status.blockedIPs.length}
- Active Threats: ${status.threats.length}

Type 'show threats' to view active threats or 'show blocked' to see blocked IPs.`;
    }
  },
  { 
    pattern: /block (?:IP )?(?:address )?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/i, 
    response: async (message: string) => {
      const ip = message.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/)?.[0];
      if (!ip) return 'Please provide a valid IP address to block.';
      
      const result = await networkService.blockIP(ip);
      return result.success 
        ? `✅ Successfully blocked IP: ${ip}`
        : `❌ Failed to block IP: ${result.message}`;
    }
  },
  { 
    pattern: /unblock (?:IP )?(?:address )?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/i, 
    response: async (message: string) => {
      const ip = message.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/)?.[0];
      if (!ip) return 'Please provide a valid IP address to unblock.';
      
      const result = await networkService.unblockIP(ip);
      return result.success 
        ? `✅ Successfully unblocked IP: ${ip}`
        : `❌ Failed to unblock IP: ${result.message}`;
    }
  },
  { 
    pattern: /show blocked|list blocked|blocked IPs/i, 
    response: async () => {
      const blockedIPs = await networkService.getBlockedIPs();
      return blockedIPs.length > 0
        ? `## Blocked IP Addresses\n${blockedIPs.map(ip => `- ${ip}`).join('\n')}`
        : 'No IP addresses are currently blocked.';
    }
  },
  { 
    pattern: /show threats|list threats|active threats/i, 
    response: async () => {
      const threats = await networkService.getActiveThreats();
      if (threats.length === 0) return 'No active threats detected.';
      
      return `## Active Threats (${threats.length})\n${threats.map(threat => 
        `### ${threat.type.toUpperCase()} - ${threat.severity.toUpperCase()}\n` +
        `- Source: ${threat.sourceIP}\n` +
        `- Description: ${threat.description}\n` +
        `- Detected: ${new Date(threat.timestamp).toLocaleString()}\n` +
        `- Status: ${threat.status}\n` +
        `- Action: Type 'mitigate ${threat.id}' to block this threat\n`
      ).join('\n')}`;
    }
  },
  { 
    pattern: /mitigate (threat-[a-z0-9-]+)/i, 
    response: async (message: string) => {
      const threatId = message.match(/mitigate (threat-[a-z0-9-]+)/i)?.[1];
      if (!threatId) return 'Please provide a valid threat ID to mitigate.';
      
      const result = await networkService.mitigateThreat(threatId);
      return result.success 
        ? `✅ ${result.message}`
        : `❌ Failed to mitigate threat: ${result.message}`;
    }
  },
  { 
    pattern: /what can you do|help/i, 
    response: `## Security Operations Assistant - Available Commands

### Network Management
- "Show network status" - Check current network status
- "Show blocked IPs" - List all blocked IP addresses
- "Block [IP address]" - Block a specific IP
- "Unblock [IP address]" - Unblock a specific IP

### Threat Management
- "Show threats" - List all active security threats
- "Mitigate [threat ID]" - Block a specific threat

### General
- "Help" - Show this help message`
  },
  { 
    pattern: /threat|attack|vulnerability|intrusion/i, 
    response: 'I can help analyze potential security threats. Type "show threats" to view active threats or describe the security concern you\'re investigating.'
  },
  { 
    pattern: /scan|check|inspect/i, 
    response: 'I can assist with security scans. Please specify what you\'d like to scan (e.g., "scan network for open ports").'
  },
  { 
    pattern: /password|credentials|auth/i, 
    response: 'For security reasons, never share passwords or credentials in chat. I can provide general guidance on authentication best practices.'
  },
  { 
    pattern: /bye|goodbye|see you/i, 
    response: 'Goodbye! Stay secure! Remember to regularly check your network status and review security logs.'
  },
];

// Fallback response generator
async function getFallbackResponse(message: string): Promise<string> {
  const lowerMessage = message.toLowerCase();
  
  // Check for exact matches first
  for (const {pattern, response} of FALLBACK_RESPONSES) {
    if (pattern.test(lowerMessage)) {
      return typeof response === 'function' 
        ? await response(message)
        : response;
    }
  }
  
  // Default fallback responses
  const defaultResponses = [
    "I'm not sure I understand. Could you provide more details about your security concern?",
    "I'm here to help with security operations. Could you clarify your question?",
    "I'm a security assistant. I can help with security analysis, threat detection, and security best practices.",
    "I'm not sure how to respond to that. Could you rephrase your question about security operations?"
  ];
  
  // Return a random default response
  return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
}

// Create and export a singleton instance
const apiKey = process.env.NEXT_PUBLIC_GROQ_API_KEY || '';

if (!apiKey) {
  console.warn('NEXT_PUBLIC_GROQ_API_KEY is not set. The chatbot will use fallback responses only.');
}

export const groqService = new GroqService(apiKey);

// Export types for use in other files
export type { GroqMessage, GroqResponse };

// Validate API key
if (!apiKey) {
  console.error('❌ NEXT_PUBLIC_GROQ_API_KEY is not set in environment variables');
  console.error('Please add NEXT_PUBLIC_GROQ_API_KEY to your .env.local file');
} else if (apiKey.startsWith('your_api_key_here') || apiKey.length < 30) {
  console.error('❌ Invalid Groq API key detected');
  console.error('Please replace the placeholder with a valid Groq API key in your .env.local file');
} else {
  console.log('✅ Groq API key loaded successfully');
}
