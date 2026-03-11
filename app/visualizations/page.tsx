"use client"

import { Sidebar } from "@/components/sidebar"
import { Visualizations } from "@/components/visualizations"

export default function VisualizationsPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Visualizations />
      </main>
    </div>
  )
}
