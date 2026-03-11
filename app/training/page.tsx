"use client"

import { Sidebar } from "@/components/sidebar"
import { Training } from "@/components/training"

export default function TrainingPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Training />
      </main>
    </div>
  )
}
