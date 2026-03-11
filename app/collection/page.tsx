"use client"

import { Sidebar } from "@/components/sidebar"
import { DataCollection } from "@/components/data-collection"

export default function CollectionPage() {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <DataCollection />
      </main>
    </div>
  )
}
