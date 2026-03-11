"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, FileText, Calendar } from "lucide-react"
import { apiClient } from "@/lib/api-client"

const API_BASE = "http://localhost:5000"

export function Reports() {
  const [reports, setReports] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data = await apiClient.get("/api/get_reports")
        setReports(data.reports || [])
      } catch (error) {
        console.error("[v0] Error fetching reports:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchReports()
  }, [])

  const handleGenerateReport = async () => {
    try {
      const data = await apiClient.post("/api/generate_report", {})
      if (data) {
        setReports((prev) => [data, ...prev])
      }
    } catch (error) {
      console.error("[v0] Error generating report:", error)
    }
  }

  const handleDownload = async (reportId: string) => {
    try {
      const blob = await apiClient.download(`/api/download_report/${reportId}`)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `report-${reportId}.pdf`
      a.click()
    } catch (error) {
      console.error("[v0] Error downloading report:", error)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border bg-card p-6">
        <h2 className="text-3xl font-bold text-foreground">Reports</h2>
        <p className="text-sm text-muted-foreground mt-1">View and download network analysis reports</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Actions */}
        <div className="flex gap-3">
          <Button onClick={handleGenerateReport} className="bg-primary hover:bg-primary/90">
            Generate Report
          </Button>
          <Button variant="outline" className="border-border bg-transparent">
            Export Data
          </Button>
        </div>

        {/* Reports List */}
        <div className="space-y-3">
          {reports.length > 0 ? (
            reports.map((report: any, idx: number) => (
              <Card key={idx} className="border-border hover:bg-muted/30 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-start gap-4 flex-1">
                      <div className="p-2 rounded-lg bg-muted">
                        <FileText className="w-5 h-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-foreground truncate">{report.name}</p>
                        <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {report.date}
                          </span>
                          <span>{report.size}</span>
                          <span className="px-2 py-1 rounded bg-muted text-foreground">{report.type}</span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownload(report.id)}
                      className="ml-2 flex items-center gap-1"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No reports available</p>
          )}
        </div>
      </div>
    </div>
  )
}
