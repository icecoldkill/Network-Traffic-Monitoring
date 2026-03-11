"use client"

import { Sidebar } from "@/components/sidebar"
import { Reports } from "@/components/reports"

export default function ReportsPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Reports />
      </main>
    </div>
  )
}
