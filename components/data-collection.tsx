"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertCircle, Play, Square } from "lucide-react"
import { apiClient } from "@/lib/api-client"

export function DataCollection() {
  const [isRunning, setIsRunning] = useState(false)
  const [sampleSize, setSampleSize] = useState(100)
  const [networkType, setNetworkType] = useState("office")
  const [includeAnomalies, setIncludeAnomalies] = useState(true)
  const [output, setOutput] = useState("")
  const [collectedData, setCollectedData] = useState(null)

  const handleStart = async () => {
    setIsRunning(true)
    setOutput(`Generating synthetic network traffic data (${sampleSize} samples)...`)
    console.log("[v0] Starting data collection with:", { sampleSize, networkType, includeAnomalies })

    try {
      console.log("[v0] Calling API endpoint: /api/generate-data")
      const data = await apiClient.post("/api/generate-data", {
        networkType: networkType,
        sampleSize: sampleSize,
        includeAnomalies: includeAnomalies,
      })

      if (data && data.status === "success") {
        setCollectedData(data.data)
        setOutput(`Collection completed. Packets captured: ${data.count}`)
        console.log("[v0] Data collection successful:", data.count, "records")
      } else {
        setOutput(
          `Error: ${data?.message || "Backend did not return expected response. Ensure Flask is running on port 5005 with /api/generate-data endpoint."}`,
        )
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Connection failed"
      setOutput(
        `Error: ${errorMsg}.\n\nTo fix this:\n1. Start your Flask backend: python api.py --port 5005\n2. Ensure /api/generate-data endpoint exists\n3. Check Flask server has no startup errors`,
      )
      console.error("[v0] Data collection error:", errorMsg)
    } finally {
      setIsRunning(false)
    }
  }

  const handleStop = async () => {
    setIsRunning(false)
    setOutput("Collection stopped.")
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card p-6">
        <h2 className="text-3xl font-bold text-foreground">Data Collection</h2>
        <p className="text-sm text-muted-foreground mt-1">Generate network traffic data</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <Card className="border-border">
          <CardHeader>
            <CardTitle>Collection Settings</CardTitle>
            <CardDescription>Configure and generate network traffic data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Network Type Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">Network Type</label>
              <select
                value={networkType}
                onChange={(e) => setNetworkType(e.target.value)}
                disabled={isRunning}
                className="w-full px-4 py-2 rounded-lg bg-muted border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="office">Office Network</option>
                <option value="datacenter">Data Center</option>
                <option value="iot">IoT Network</option>
                <option value="home">Home Network</option>
              </select>
            </div>

            {/* Sample Size */}
            <div>
              <label className="block text-sm font-medium mb-2">Sample Size (packets)</label>
              <input
                type="number"
                value={sampleSize}
                onChange={(e) => setSampleSize(Number.parseInt(e.target.value))}
                disabled={isRunning}
                min={10}
                max={5000}
                className="w-full px-4 py-2 rounded-lg bg-muted border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            {/* Include Anomalies */}
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="anomalies"
                checked={includeAnomalies}
                onChange={(e) => setIncludeAnomalies(e.target.checked)}
                disabled={isRunning}
                className="w-4 h-4 rounded border border-border"
              />
              <label htmlFor="anomalies" className="text-sm font-medium">
                Include Anomalous Traffic Patterns
              </label>
            </div>

            {/* Controls */}
            <div className="flex gap-3">
              <Button
                onClick={handleStart}
                disabled={isRunning}
                className="flex items-center gap-2 bg-primary hover:bg-primary/90"
              >
                <Play className="w-4 h-4" />
                Start Generation
              </Button>
              <Button
                onClick={handleStop}
                disabled={!isRunning}
                variant="outline"
                className="flex items-center gap-2 bg-transparent"
              >
                <Square className="w-4 h-4" />
                Stop
              </Button>
            </div>

            {/* Status */}
            <div className="p-4 rounded-lg bg-muted border border-border">
              <p className="text-sm font-mono text-muted-foreground">{output || "Ready to generate data"}</p>
              {isRunning && (
                <div className="mt-3 w-full bg-border rounded-full h-1 overflow-hidden">
                  <div className="bg-primary h-full animate-pulse" style={{ width: "45%" }} />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="border-border border-yellow-500/30 bg-yellow-500/5">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              Collection Tips
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>• Choose a network type that matches your testing scenario</p>
            <p>• Larger sample sizes provide better accuracy for anomaly detection</p>
            <p>• Data is automatically generated with synthetic network patterns</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
