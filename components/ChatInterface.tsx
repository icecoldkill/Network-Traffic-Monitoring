'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, X, Shield, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { groqService } from '@/services/groqService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  type?: 'info' | 'warning' | 'error' | 'success';
  isLoading?: boolean;
  action?: {
    type: string;
    params?: Record<string, any>;
  };
}

export default function ChatInterface({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  // Auto-scroll when new messages arrive
  useEffect(() => {
    scrollToBottom('auto');
  }, [messages]);

  // Focus input on load
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Initialize with welcome message
  useEffect(() => {
    if (!isInitialized && messages.length === 0) {
      setMessages([
        {
          id: Date.now(),
          text: 'Hello! I\'m your Security Assistant. How can I help you with your security operations today?',
          sender: 'bot',
          timestamp: new Date(),
          type: 'info'
        }
      ]);
      setIsInitialized(true);
    }
  }, [isInitialized, messages.length]);

  const generateUniqueId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const addMessage = (text: string, sender: 'user' | 'assistant', type: Message['type'] = 'info') => {
    const newMessage: Message = {
      id: generateUniqueId(),
      text,
      sender,
      timestamp: new Date(),
      type,
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const updateLastMessage = (text: string, type?: Message['type']) => {
    setMessages(prev => {
      const newMessages = [...prev];
      const lastMessage = newMessages[newMessages.length - 1];
      if (lastMessage) {
        lastMessage.text = text;
        if (type) lastMessage.type = type;
        lastMessage.isLoading = false;
      }
      return newMessages;
    });
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;

    setIsProcessing(true);
    const userMessage: Message = {
      id: Date.now(),
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Add loading message
    const loadingMessage: Message = {
      id: Date.now() + 1,
      text: 'Thinking...',
      sender: 'bot',
      isLoading: true,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, loadingMessage]);

    try {
      const response = await groqService.chat(input, conversationHistory);
      
      if (response.error) {
        throw new Error(response.error || 'Failed to process your request');
      }

      setConversationHistory(response.conversation_history);

      // Remove loading message and add bot's response
      setMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        {
          id: Date.now() + 2,
          text: response.response || 'I apologize, but I encountered an issue processing your request.',
          sender: 'bot',
          timestamp: new Date()
        }
      ]);
    } catch (err) {
      const error = err as Error;
      console.error('Error sending message:', error);
      
      // Remove loading message and show error
      setMessages(prev => [
        ...prev.filter(m => !m.isLoading),
        {
          id: Date.now() + 2,
          text: `I apologize, but I encountered an error: ${error.message}`,
          sender: 'bot',
          type: 'error',
          timestamp: new Date()
        }
      ]);
      
      toast.error('Failed to send message', {
        description: error.message,
        duration: 5000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Helper function to create bot messages
  const createBotMessage = (text: string, type: 'info' | 'warning' | 'error' | 'success' = 'info', action?: any): Message => {
    return {
      id: Date.now(),
      text,
      sender: 'bot',
      timestamp: new Date(),
      type,
      action
    };
  };

  // Mock security functions
  const checkNetworkStatus = async (): Promise<Message> => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // Generate a random network status
    const status = Math.random() > 0.2 ? 'secure' : 'vulnerable';
    const threats = status === 'secure' ? 0 : Math.floor(Math.random() * 5) + 1;
    
    if (status === 'secure') {
      return createBotMessage(
        '✅ Network status: Secure\n' +
        'No active threats detected. All systems are operating normally.',
        'success'
      );
    } else {
      return createBotMessage(
        `⚠️ Network status: Vulnerable\n` +
        `Detected ${threats} potential security ${threats === 1 ? 'threat' : 'threats'}. ` +
        'Run a security scan for more details.',
        'warning'
      );
    }
  };

  const threatsList = (): string => {
    const threats = [
      'Suspicious login attempt from unknown IP',
      'Outdated security certificates',
      'Unpatched system vulnerabilities',
      'Unusual outbound traffic detected',
      'Multiple failed login attempts'
    ];
    
    return threats
      .sort(() => Math.random() - 0.5)
      .slice(0, Math.floor(Math.random() * 3) + 1)
      .map((t, i) => `• ${t}`)
      .join('\n');
  };

  const runNetworkScan = async (): Promise<Message> => {
    // Simulate scanning
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Generate random scan results
    const hasThreats = Math.random() > 0.3;
    const threats = hasThreats ? threatsList() : 'No critical issues found';
    const status = hasThreats ? 'warning' : 'success';
    
    setIsProcessing(false);
    
    return createBotMessage(
      `🔍 Network Scan Results:\n\n` +
      `Status: ${hasThreats ? 'Issues Found' : 'Secure'}\n` +
      `Details: ${threats}\n\n` +
      `Last scanned: ${new Date().toLocaleTimeString()}`,
      status as 'warning' | 'success'
    );
  };

  const blockIP = async (ip: string): Promise<Message> => {
    try {
      const response = await groqService.chat(`Block IP ${ip}`, conversationHistory);
      setConversationHistory(response.conversation_history);
      return createBotMessage(
        `✅ Successfully blocked IP: ${ip}\n` +
        `This IP has been added to the firewall blacklist.`,
        'success'
      );
    } catch (error) {
      console.error('Error blocking IP:', error);
      return createBotMessage(
        '❌ Failed to block IP. Please try again later or contact support.',
        'error'
      );
    }
  };

  // Render message with appropriate styling based on type
  const renderMessageContent = (message: Message) => {
    const baseStyles = "px-4 py-2 rounded-lg text-sm";
    let messageStyles = "";
    
    if (message.sender === 'user') {
      messageStyles = "bg-indigo-600 text-white rounded-tr-none";
    } else {
      switch (message.type) {
        case 'warning':
          messageStyles = "bg-yellow-50 text-yellow-800 border-l-4 border-yellow-400";
          break;
        case 'error':
          messageStyles = "bg-red-50 text-red-800 border-l-4 border-red-400";
          break;
        case 'success':
          messageStyles = "bg-green-50 text-green-800 border-l-4 border-green-400";
          break;
        default:
          messageStyles = "bg-white text-gray-800 shadow";
      }
    }

    const formatMessage = (text: string) => {
      return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
        .replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold mt-2 mb-1">$1</h3>')
        .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold mt-3 mb-2">$1</h2>')
        .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-4 mb-3">$1</h1>')
        .replace(/\n/g, '<br/>');
    };

    return (
      <div 
        className={`${baseStyles} ${messageStyles} whitespace-pre-wrap`}
        dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
      />
    );
  };

  const handleAction = async (action: any) => {
    if (action.type === 'block' && action.params?.ip) {
      await blockIP(action.params.ip);
    }
  };

  const getActionButtonText = (actionType: string) => {
    switch (actionType) {
      case 'block':
        return 'Block IP';
      case 'scan':
        return 'Run Scan';
      case 'analyze':
        return 'Analyze';
      case 'report':
        return 'View Report';
      default:
        return 'Take Action';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gradient-to-r from-blue-600 to-blue-700">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="h-5 w-5 text-white" />
          <h2 className="font-semibold text-white">Security Assistant</h2>
        </div>
        <Button 
          variant="ghost" 
          size="icon"
          onClick={onClose}
          className="text-white hover:bg-blue-500 h-8 w-8"
          aria-label="Close chat"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex',
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  'flex max-w-[85%] rounded-lg p-3 relative',
                  message.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-100 text-gray-800 rounded-bl-none',
                  message.type === 'error' && 'bg-red-50 border border-red-200',
                  message.isLoading && 'bg-gray-50 text-gray-500'
                )}
              >
                {message.isLoading ? (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>{message.text}</span>
                  </div>
                ) : (
                  <>
                    <div className="flex-shrink-0 mr-2">
                      {message.sender === 'user' ? (
                        <User className="h-5 w-5" />
                      ) : message.type === 'error' ? (
                        <AlertCircle className="h-5 w-5 text-red-500" />
                      ) : (
                        <Bot className="h-5 w-5 text-blue-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm whitespace-pre-wrap">{message.text}</div>
                      <div 
                        className={cn(
                          'text-xs mt-1',
                          message.sender === 'user' ? 'text-blue-200' : 'text-gray-500'
                        )}
                      >
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <form onSubmit={handleSend} className="p-4 border-t bg-gray-50">
        {error && (
          <div className="mb-3 p-2 text-sm text-red-600 bg-red-50 rounded-md">
            {error}
          </div>
        )}
        <div className="flex space-x-2">
          <Input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about security, threats, or network status..."
            className="flex-1"
            disabled={isProcessing}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(e);
              }
            }}
          />
          <Button 
            type="submit" 
            disabled={!input.trim() || isProcessing}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Send className="h-4 w-4 mr-2" />
            )}
            {isProcessing ? 'Sending...' : 'Send'}
          </Button>
        </div>
        <p className="mt-2 text-xs text-gray-500 text-center">
          Ask about security alerts, network status, or request a security scan
        </p>
      </form>
    </div>
  );
}
