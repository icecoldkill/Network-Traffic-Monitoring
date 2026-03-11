"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { MessageSquare, Send, Loader2 } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm your Security Operations AI assistant. I can help you analyze network traffic, detect anomalies, and provide security recommendations. Ask me about threats, best practices, or analyze specific security incidents.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [backendStatus, setBackendStatus] = useState("checking")
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    checkBackendStatus()
  }, [])

  const checkBackendStatus = async () => {
    try {
      const response = await fetch("/api/proxy?endpoint=/api/health", {
        method: "GET",
      })
      setBackendStatus(response.ok ? "connected" : "offline")
    } catch {
      setBackendStatus("offline")
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setLoading(true)

    try {
      const response = await fetch("/api/proxy?endpoint=/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: input,
          conversation_history: messages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      })

      const data = await response.json()

      if (response.ok && data.response) {
        const assistantMessage: Message = {
          role: "assistant",
          content: data.response,
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, assistantMessage])
      } else if (data.status === "offline") {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "Backend is offline. Make sure your Flask server is running on port 5000. I can still help with general security questions!",
            timestamp: new Date(),
          },
        ])
        setBackendStatus("offline")
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.message || "Error processing your request. Please try again.",
            timestamp: new Date(),
          },
        ])
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Connection error: ${err instanceof Error ? err.message : "Unknown error"}. Check if the backend is running.`,
          timestamp: new Date(),
        },
      ])
      setBackendStatus("offline")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 space-y-8 h-screen flex flex-col">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <MessageSquare className="w-8 h-8 text-cyan-500" />
          Security AI Assistant
        </h1>
        <p className="text-muted-foreground">AI-powered security analysis powered by Groq LLM</p>
        <div className="flex items-center gap-2 text-sm">
          <div
            className={`w-2 h-2 rounded-full ${backendStatus === "connected" ? "bg-green-500" : backendStatus === "offline" ? "bg-red-500" : "bg-yellow-500"}`}
          />
          <span className="text-muted-foreground">
            {backendStatus === "connected"
              ? "Backend Connected"
              : backendStatus === "offline"
                ? "Backend Offline - Using local responses"
                : "Checking backend..."}
          </span>
        </div>
      </div>

      <Card className="flex-1 flex flex-col">
        <CardHeader>
          <CardTitle>Chat</CardTitle>
          <CardDescription>Ask me anything about network security, anomalies, or threats</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-lg rounded-lg px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-cyan-600 text-white"
                      : "bg-slate-800 border border-slate-700 text-slate-100"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <p className={`text-xs mt-1 ${msg.role === "user" ? "opacity-70" : "text-slate-400"}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2">
                  <Loader2 className="w-4 h-4 animate-spin text-cyan-500" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="Ask about network security..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
              disabled={loading}
              className="bg-slate-900 border-slate-700"
            />
            <Button onClick={handleSendMessage} disabled={loading || !input.trim()} size="icon">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
