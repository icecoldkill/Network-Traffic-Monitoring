"use client"

import { useEffect, useState } from "react"
import { AlertCircle, CheckCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

export function BackendStatus() {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch("http://localhost:5005/", {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        })
        setIsConnected(response.ok)
      } catch (error) {
        setIsConnected(false)
      } finally {
        setIsLoading(false)
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 5000)
    return () => clearInterval(interval)
  }, [])

  if (isLoading) {
    return null
  }

  if (!isConnected) {
    return (
      <Alert className="border-red-500 bg-red-50 mb-6">
        <AlertCircle className="h-4 w-4 text-red-600" />
        <AlertDescription className="text-red-800 ml-2">
          <div className="font-semibold">Backend not connected</div>
          <div className="text-sm mt-2">
            Your Flask API is not running. To start it, open a terminal in your project directory and run:
          </div>
          <div className="bg-gray-900 text-white p-3 rounded mt-2 font-mono text-sm overflow-x-auto">
            python api.py --port 5005
          </div>
          <div className="text-sm mt-2">
            The backend should start on <code className="bg-gray-200 px-2 py-1 rounded">http://localhost:5005</code>
          </div>
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <Alert className="border-green-500 bg-green-50 mb-6">
      <CheckCircle className="h-4 w-4 text-green-600" />
      <AlertDescription className="text-green-800 ml-2">
        <div className="font-semibold">Backend connected successfully</div>
        <div className="text-sm">Your Flask API on port 5005 is running and ready to use.</div>
      </AlertDescription>
    </Alert>
  )
}
