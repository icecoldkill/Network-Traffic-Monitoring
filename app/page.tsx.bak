"use client"

import { useState, useEffect } from "react"
import { Sidebar } from "@/components/sidebar"
import { BackendStatus } from "@/components/backend-status"
import { Dashboard } from "@/components/dashboard"
import { DataCollection } from "@/components/data-collection"
import { Visualizations } from "@/components/visualizations"
import { Anomalies } from "@/components/anomalies"
import { Training } from "@/components/training"
import { Reports } from "@/components/reports"
import { ChatPanel } from "@/components/chat/ChatPanel"
import { SetupGuide } from "@/components/setup-guide"
import { LiveTrafficAnalysis } from "@/components/live-traffic/LiveTrafficAnalysis"

type Page = "dashboard" | "collect" | "visualize" | "anomalies" | "training" | "reports" | "live-traffic"

export default function Home() {
  const [currentPage, setCurrentPage] = useState<Page>("dashboard")

  return (
    <div className="flex h-screen bg-background">
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="flex-1 overflow-auto">
        <div className="p-6 pt-6 space-y-4">
          <SetupGuide />
          <BackendStatus />
        </div>

        <div className="px-6 pb-6 relative">
          {currentPage === "dashboard" && <Dashboard />}
          {currentPage === "collect" && <DataCollection />}
          {currentPage === "visualize" && <Visualizations />}
          {currentPage === "anomalies" && <Anomalies />}
          {currentPage === "training" && <Training />}
          {currentPage === "reports" && <Reports />}
          {currentPage === "live-traffic" && <LiveTrafficAnalysis />}
          
          {/* Always show chat panel */}
          <ChatPanel />
        </div>
      </main>
    </div>
  )
}
