"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Activity, BarChart3, Zap, Network, Brain, FileText, Settings, Radio } from "lucide-react"

const navigation = [
  { name: "Dashboard", href: "/", icon: Activity },
  { name: "Live Traffic", href: "/live-traffic", icon: Radio },
  { name: "Data Collection", href: "/collection", icon: Network },
  { name: "Visualizations", href: "/visualizations", icon: BarChart3 },
  { name: "Anomaly Detection", href: "/anomalies", icon: Zap },
  { name: "Model Training", href: "/training", icon: Brain },
  { name: "Reports", href: "/reports", icon: FileText },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 border-r border-border bg-card">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary">
              <Activity className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-semibold text-lg">NetWatch</h1>
              <p className="text-xs text-muted-foreground">Traffic Monitor</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                  isActive 
                    ? "bg-primary/10 text-primary border-l-4 border-primary" 
                    : "text-foreground hover:bg-muted"
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm font-medium">{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <div className="text-xs text-muted-foreground text-center">
            <p>v1.0.0</p>
            <p>Real-time Monitoring</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
