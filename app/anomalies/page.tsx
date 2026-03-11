"use client"

import { Sidebar } from "@/components/sidebar"
import { Anomalies } from "@/components/anomalies"

export default function AnomaliesPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Anomalies />
      </main>
    </div>
  )
}
