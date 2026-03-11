import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Gauge, Shield, Activity, Zap, Server, AlertOctagon } from "lucide-react"
import { Progress } from "@/components/ui/progress"

type ThreatLevel = 'low' | 'medium' | 'high' | 'critical'

interface MetricsCardsProps {
  metrics: {
    anomalies: number
    avgPackets: number
    totalTraffic: string
    errorRate: string
    threatLevel: ThreatLevel
    devicesOnline: number
    threatsBlocked: number
    avgResponseTime: number
    securityScore: number
  }
  loading?: boolean
}

const getThreatLevelColor = (level: ThreatLevel) => {
  switch (level) {
    case 'low': return 'bg-blue-500'
    case 'medium': return 'bg-amber-500'
    case 'high': return 'bg-red-500'
    case 'critical': return 'bg-violet-600'
    default: return 'bg-gray-500'
  }
}

export function MetricsCards({ metrics, loading = false }: MetricsCardsProps) {
  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-6 bg-gray-200 rounded-full" />
            </CardHeader>
            <CardContent>
              <div className="h-4 w-24 bg-gray-200 rounded animate-pulse mt-2" />
              <div className="h-2 w-full bg-gray-100 rounded-full mt-4" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Security Score */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Security Score</CardTitle>
          <Shield className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.securityScore}</div>
          <div className="mt-2">
            <Progress value={metrics.securityScore} className="h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              {metrics.securityScore > 80 ? 'Excellent' : metrics.securityScore > 60 ? 'Good' : 'Needs attention'}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Active Threats */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Threats</CardTitle>
          <AlertOctagon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.anomalies}</div>
          <div className="flex items-center mt-1">
            <div className={`h-2 w-2 rounded-full ${getThreatLevelColor(metrics.threatLevel)} mr-2`} />
            <p className="text-xs text-muted-foreground capitalize">
              {metrics.threatLevel} threat level
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Network Performance */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Network Performance</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.avgResponseTime}ms</div>
          <p className="text-xs text-muted-foreground">
            {metrics.avgResponseTime < 30 ? 'Excellent' : metrics.avgResponseTime < 100 ? 'Good' : 'Needs attention'}
          </p>
        </CardContent>
      </Card>

      {/* Devices Online */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Devices Online</CardTitle>
          <Server className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.devicesOnline}</div>
          <p className="text-xs text-muted-foreground">
            {metrics.threatsBlocked} threats blocked today
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
