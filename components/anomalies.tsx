"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle } from "lucide-react"
import { apiClient } from "@/lib/api-client"

export function Anomalies() {
  const [anomalies, setAnomalies] = useState<any[]>([])
  const [stats, setStats] = useState({ critical: 0, warnings: 0, total: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const data = await apiClient.get("/api/get_anomalies")
        const anomaliesList = data.anomalies || []
        setAnomalies(anomaliesList)

        const criticalCount = anomaliesList.filter((a: any) => a.severity === "critical").length
        const warningCount = anomaliesList.filter((a: any) => a.severity === "warning").length
        setStats({ critical: criticalCount, warnings: warningCount, total: anomaliesList.length })
      } catch (error) {
        console.error("[v0] Error fetching anomalies:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchAnomalies()
    const interval = setInterval(fetchAnomalies, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card p-6">
        <h2 className="text-3xl font-bold text-foreground">Anomaly Detection</h2>
        <p className="text-sm text-muted-foreground mt-1">Detected network anomalies and suspicious activities</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Critical</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-destructive">{stats.critical}</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-yellow-500">{stats.warnings}</p>
            </CardContent>
          </Card>
          <Card className="border-border">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Detected</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{stats.total}</p>
            </CardContent>
          </Card>
        </div>

        {/* Anomalies List */}
        <Card className="border-border">
          <CardHeader>
            <CardTitle>Recent Anomalies</CardTitle>
            <CardDescription>Network anomalies detected by ML model</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {anomalies.length > 0 ? (
                anomalies.map((anomaly: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <AlertTriangle
                          className={`w-5 h-5 ${
                            anomaly.severity === "critical" ? "text-destructive" : "text-yellow-500"
                          }`}
                        />
                        <div>
                          <p className="font-semibold text-foreground">{anomaly.type}</p>
                          <p className="text-xs text-muted-foreground">{anomaly.timestamp || anomaly.time}</p>
                        </div>
                      </div>
                      <Badge variant={anomaly.severity === "critical" ? "destructive" : "secondary"}>
                        {anomaly.severity.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-3 text-xs text-muted-foreground">
                      <div>
                        <p className="opacity-70">Packets</p>
                        <p className="font-mono font-semibold text-foreground">{anomaly.packets || 0}</p>
                      </div>
                      <div>
                        <p className="opacity-70">Bytes</p>
                        <p className="font-mono font-semibold text-foreground">{anomaly.bytes || "0B"}</p>
                      </div>
                      <div>
                        <p className="opacity-70">Protocol</p>
                        <p className="font-mono font-semibold text-foreground">{anomaly.protocol || "N/A"}</p>
                      </div>
                      <div className="md:col-span-2">
                        <p className="opacity-70">Source IP</p>
                        <p className="font-mono font-semibold text-foreground">
                          {anomaly.source_ip || anomaly.source || "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No anomalies detected</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
