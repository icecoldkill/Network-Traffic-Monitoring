"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart, Bar, LineChart, Line, ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip } from "recharts"
import { apiClient } from "@/lib/api-client"

// Mock visualization data
const heatmapData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  traffic: Math.floor(Math.random() * 1000) + 200,
}))

export function Visualizations() {
  const [visType, setVisType] = useState("heatmap")
  const [loading, setLoading] = useState(false)
  const [visualizations, setVisualizations] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!visualizations[visType]) {
      generateVisualization(visType)
    }
  }, [visType])

  const generateVisualization = async (vizType: string) => {
    setLoading(true)
    console.log("[v0] Generating visualization:", vizType)

    try {
      // Mock traffic data for visualization
      const mockData = [
        {
          timestamp: "2024-01-15 10:00:00",
          protocol: "TCP",
          source_ip: "192.168.1.100",
          dest_ip: "192.168.1.1",
          bytes_sent: 1500,
          bytes_received: 2000,
          packet_count: 45,
          duration: 2.5,
          anomaly_score: 0.1,
        },
        {
          timestamp: "2024-01-15 10:00:05",
          protocol: "UDP",
          source_ip: "192.168.1.101",
          dest_ip: "192.168.1.1",
          bytes_sent: 800,
          bytes_received: 1200,
          packet_count: 30,
          duration: 1.8,
          anomaly_score: 0.2,
        },
      ]

      const response = await apiClient.post("/api/visualize", {
        data: mockData,
        type: vizType === "timeseries" ? "time-series" : vizType,
      })

      if (response && response.status === "success") {
        setVisualizations((prev) => ({
          ...prev,
          [vizType]: `data:image/png;base64,${response.image}`,
        }))
        console.log("[v0] Visualization generated successfully")
      } else {
        console.error("[v0] Visualization error:", response?.message)
      }
    } catch (error) {
      console.error("[v0] Error generating visualization:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card p-6">
        <h2 className="text-3xl font-bold text-foreground">Visualizations</h2>
        <p className="text-sm text-muted-foreground mt-1">View network traffic patterns and insights</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Controls */}
        <div className="flex gap-2">
          {[
            { id: "heatmap", label: "Heatmap" },
            { id: "timeseries", label: "Time Series" },
            { id: "spectrogram", label: "Distribution" },
          ].map((type) => (
            <Button
              key={type.id}
              onClick={() => setVisType(type.id)}
              variant={visType === type.id ? "default" : "outline"}
              className="border-border"
              disabled={loading}
            >
              {type.label}
            </Button>
          ))}
        </div>

        {/* Heatmap View */}
        {visType === "heatmap" && (
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Traffic Heatmap (24h)</CardTitle>
              <CardDescription>Hourly traffic distribution {loading && "- Loading..."}</CardDescription>
            </CardHeader>
            <CardContent>
              {visualizations.heatmap ? (
                <img src={visualizations.heatmap || "/placeholder.svg"} alt="Heatmap" className="w-full rounded-lg" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={heatmapData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="hour" stroke="var(--color-muted-foreground)" />
                    <YAxis stroke="var(--color-muted-foreground)" />
                    <Tooltip contentStyle={{ backgroundColor: "var(--color-card)", border: "none" }} />
                    <Bar dataKey="traffic" fill="var(--color-chart-2)" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Time Series View */}
        {visType === "timeseries" && (
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Time Series Analysis</CardTitle>
              <CardDescription>Network activity trend {loading && "- Loading..."}</CardDescription>
            </CardHeader>
            <CardContent>
              {visualizations.timeseries ? (
                <img
                  src={visualizations.timeseries || "/placeholder.svg"}
                  alt="Time Series"
                  className="w-full rounded-lg"
                />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={heatmapData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="hour" stroke="var(--color-muted-foreground)" />
                    <YAxis stroke="var(--color-muted-foreground)" />
                    <Tooltip contentStyle={{ backgroundColor: "var(--color-card)", border: "none" }} />
                    <Line type="monotone" dataKey="traffic" stroke="var(--color-primary)" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        )}

        {/* Distribution View */}
        {visType === "spectrogram" && (
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Traffic Distribution</CardTitle>
              <CardDescription>Peak hours and patterns {loading && "- Loading..."}</CardDescription>
            </CardHeader>
            <CardContent>
              {visualizations.spectrogram ? (
                <img
                  src={visualizations.spectrogram || "/placeholder.svg"}
                  alt="Distribution"
                  className="w-full rounded-lg"
                />
              ) : (
                <div className="space-y-4">
                  {heatmapData.slice(0, 12).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <span className="text-sm w-12 text-muted-foreground">{item.hour}</span>
                      <div className="flex-1 h-6 bg-muted rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-primary to-secondary rounded-lg"
                          style={{ width: `${(item.traffic / 1000) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-mono text-muted-foreground">{item.traffic}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
