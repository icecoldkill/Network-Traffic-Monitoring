"use client"

import { AlertCircle, CheckCircle, Terminal } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useEffect, useState } from "react"

export function SetupGuide() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking")

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch("http://localhost:5005", { method: "HEAD" })
        if (response.ok) {
          setBackendStatus("online")
        }
      } catch {
        setBackendStatus("offline")
      }
    }

    checkBackend()
    const interval = setInterval(checkBackend, 3000)
    return () => clearInterval(interval)
  }, [])

  if (backendStatus === "online") {
    return (
      <Alert className="bg-green-50 border-green-200">
        <CheckCircle className="h-4 w-4 text-green-600" />
        <AlertTitle className="text-green-900">Backend Connected</AlertTitle>
        <AlertDescription className="text-green-800">
          Flask API is running on port 5005. Dashboard will display live data.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <Card className="bg-destructive/5 border-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertCircle className="w-5 h-5" />
          Backend Not Connected
        </CardTitle>
        <CardDescription>Flask API is not running. Follow these steps to start it.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-muted">
            <p className="text-sm font-medium mb-2">Step 1: Open a terminal in your Flask project directory</p>
            <div className="bg-black text-green-400 p-3 rounded font-mono text-xs">
              $ cd /path/to/your/flask/project
            </div>
          </div>

          <div className="p-3 rounded-lg bg-muted">
            <p className="text-sm font-medium mb-2">Step 2: Start the Flask API on port 5005</p>
            <div className="bg-black text-green-400 p-3 rounded font-mono text-xs">$ python api.py --port 5005</div>
          </div>

          <div className="p-3 rounded-lg bg-muted">
            <p className="text-sm font-medium mb-2">Expected output:</p>
            <div className="bg-black text-green-400 p-3 rounded font-mono text-xs">
              {`* Running on http://localhost:5005
* WARNING: This is a development server`}
            </div>
          </div>
        </div>

        <Alert>
          <Terminal className="h-4 w-4" />
          <AlertTitle>Checking...</AlertTitle>
          <AlertDescription>
            This page will automatically detect when your Flask backend starts on port 5005.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  )
}
