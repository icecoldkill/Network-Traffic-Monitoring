"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { 
  AlertCircle, 
  AlertTriangle, 
  BarChart2, 
  Bell, 
  Clock, 
  Download, 
  Filter, 
  Gauge, 
  Globe, 
  HardDrive, 
  HelpCircle, 
  Network, 
  RefreshCw, 
  Search, 
  Server, 
  Settings, 
  Shield, 
  ShieldAlert, 
  ShieldCheck, 
  Sliders, 
  TrendingUp, 
  Users, 
  Zap 
} from "lucide-react"

// Import our new components
import { MetricsCards } from "./dashboard/MetricsCards"
import { TrafficChart } from "./dashboard/TrafficChart"
import { SecurityEvents } from "./dashboard/SecurityEvents"

// Types
type ThreatLevel = 'low' | 'medium' | 'high' | 'critical'

interface SecurityEvent {
  id: string
  type: string
  severity: ThreatLevel
  source: string
  timestamp: string
  description: string
  status: 'new' | 'investigating' | 'resolved'
}

interface NetworkDevice {
  id: string
  name: string
  ip: string
  type: 'server' | 'firewall' | 'switch' | 'endpoint'
  status: 'online' | 'offline' | 'warning'
  lastSeen: string
  traffic: number
  threats: number
}

interface DashboardData {
  trafficData: Array<{
    time: string
    traffic: number
    threats: number
    anomalies: number
  }>
  bandwidthData: Array<{
    time: string
    incoming: number
    outgoing: number
  }>
  protocolData: Array<{
    name: string
    value: number
  }>
  recentAnomalies: any[]
  securityEvents: SecurityEvent[]
  networkDevices: NetworkDevice[]
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
  lastUpdated: string
}

// Mock data generator
const generateMockData = (): DashboardData => {
  const now = new Date()
  const trafficData = Array.from({ length: 24 }, (_, i) => ({
    time: `${String(i).padStart(2, '0')}:00`,
    traffic: Math.floor(Math.random() * 1000) + 500,
    threats: Math.floor(Math.random() * 50),
    anomalies: Math.floor(Math.random() * 20)
  }))

  const bandwidthData = Array.from({ length: 24 }, (_, i) => ({
    time: `${String(i).padStart(2, '0')}:00`,
    incoming: Math.floor(Math.random() * 500) + 100,
    outgoing: Math.floor(Math.random() * 300) + 50
  }))

  const protocolData = [
    { name: 'HTTP', value: 45 },
    { name: 'HTTPS', value: 30 },
    { name: 'SSH', value: 10 },
    { name: 'FTP', value: 5 },
    { name: 'DNS', value: 10 }
  ]

  const securityEvents: SecurityEvent[] = Array.from({ length: 10 }, (_, i) => ({
    id: `event-${i}`,
    type: ['Unauthorized Access', 'DDoS', 'Malware', 'Phishing', 'Data Exfiltration'][i % 5],
    severity: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)] as ThreatLevel,
    source: `192.168.1.${Math.floor(Math.random() * 255)}`,
    timestamp: new Date(now.getTime() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
    description: 'Potential security threat detected',
    status: ['new', 'investigating', 'resolved'][Math.floor(Math.random() * 3)] as SecurityEvent['status']
  }))

  const networkDevices: NetworkDevice[] = Array.from({ length: 8 }, (_, i) => ({
    id: `device-${i}`,
    name: `Device ${String.fromCharCode(65 + i)}`,
    ip: `192.168.1.${i + 1}`,
    type: ['server', 'firewall', 'switch', 'endpoint'][i % 4] as NetworkDevice['type'],
    status: ['online', 'offline', 'warning'][Math.floor(Math.random() * 3)] as NetworkDevice['status'],
    lastSeen: new Date(now.getTime() - Math.random() * 24 * 60 * 60 * 1000).toISOString(),
    traffic: Math.floor(Math.random() * 1000),
    threats: Math.floor(Math.random() * 10)
  }))

  const totalThreats = securityEvents.length
  const criticalThreats = securityEvents.filter(e => e.severity === 'critical').length
  const devicesOnline = networkDevices.filter(d => d.status === 'online').length
  const securityScore = Math.max(0, 100 - (criticalThreats * 10) - (totalThreats * 2))

  return {
    trafficData,
    bandwidthData,
    protocolData,
    recentAnomalies: securityEvents.slice(0, 5),
    securityEvents,
    networkDevices,
    metrics: {
      anomalies: securityEvents.length,
      avgPackets: Math.floor(Math.random() * 5000) + 1000,
      totalTraffic: `${(Math.random() * 1000).toFixed(2)} GB`,
      errorRate: `${(Math.random() * 5).toFixed(2)}%`,
      threatLevel: criticalThreats > 0 ? 'critical' : totalThreats > 5 ? 'high' : totalThreats > 2 ? 'medium' : 'low',
      devicesOnline,
      threatsBlocked: Math.floor(Math.random() * 100),
      avgResponseTime: parseFloat((Math.random() * 50 + 10).toFixed(2)),
      securityScore
    },
    lastUpdated: now.toISOString()
  }
}

export function Dashboard() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [timeRange, setTimeRange] = useState('24h')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  
  // Filtered data based on search query
  const filteredEvents = dashboardData?.securityEvents.filter(event => 
    event.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    event.source.includes(searchQuery) ||
    event.severity.includes(searchQuery.toLowerCase())
  ) || []

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    setLoading(true)
    try {
      // In a real app, we would fetch this from the API
      // const response = await apiClient.get('/dashboard')
      // setDashboardData(response.data)
      
      // For now, use mock data
      const mockData = generateMockData()
      setDashboardData(mockData)
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      // Fallback to mock data if API fails
      setDashboardData(generateMockData())
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-refresh data
  useEffect(() => {
    fetchDashboardData()
    
    let intervalId: NodeJS.Timeout
    if (autoRefresh) {
      intervalId = setInterval(fetchDashboardData, 30000) // Refresh every 30 seconds
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [autoRefresh, fetchDashboardData])
  
  // Handle view details for security events
  const handleViewEventDetails = (event: SecurityEvent) => {
    // In a real app, this would open a modal or navigate to a details page
    console.log('Viewing event details:', event)
    alert(`Event Details:\n\nType: ${event.type}\nSeverity: ${event.severity}\nSource: ${event.source}\nStatus: ${event.status}`)
  }

  // Render loading state
  if (!dashboardData) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Security Dashboard</h1>
            <p className="text-muted-foreground">Loading security data...</p>
          </div>
          <div className="flex items-center space-x-2">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-32" />
          </div>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Skeleton className="col-span-4 h-[400px]" />
          <Skeleton className="col-span-3 h-[400px]" />
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Skeleton className="col-span-4 h-[400px]" />
          <Skeleton className="col-span-3 h-[400px]" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between space-y-2 md:flex-row md:items-center md:space-y-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Security Dashboard</h1>
          <p className="text-muted-foreground">
            Last updated: {new Date(dashboardData.lastUpdated).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4" />
            <span>Auto-refresh</span>
            <Switch 
              checked={autoRefresh} 
              onCheckedChange={setAutoRefresh} 
              className="ml-2"
            />
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchDashboardData}
            disabled={loading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>
      
      {/* Metrics Cards */}
      <MetricsCards 
        metrics={dashboardData.metrics} 
        loading={loading} 
      />
      
      {/* Traffic and Bandwidth Charts */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <TrafficChart 
          data={dashboardData.trafficData} 
          loading={loading} 
        />
        
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Bandwidth Usage</CardTitle>
            <CardDescription>Incoming vs Outgoing Traffic</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={dashboardData.bandwidthData}
                  margin={{
                    top: 10,
                    right: 30,
                    left: 0,
                    bottom: 0,
                  }}
                >
                  <defs>
                    <linearGradient id="colorIncoming" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
                    </linearGradient>
                    <linearGradient id="colorOutgoing" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#82ca9d" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis 
                    dataKey="time" 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis 
                    yAxisId="left" 
                    orientation="left" 
                    stroke="#8884d8" 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis 
                    yAxisId="right" 
                    orientation="right" 
                    stroke="#82ca9d" 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="incoming"
                    stroke="#8884d8"
                    fillOpacity={1}
                    fill="url(#colorIncoming)"
                    name="Incoming"
                  />
                  <Area
                    yAxisId="right"
                    type="monotone"
                    dataKey="outgoing"
                    stroke="#82ca9d"
                    fillOpacity={1}
                    fill="url(#colorOutgoing)"
                    name="Outgoing"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Security Events and Protocol Distribution */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Security Events</CardTitle>
                <CardDescription>Recent security events and threats</CardDescription>
              </div>
              <div className="relative w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Filter events..."
                  className="pl-8 h-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <SecurityEvents 
              events={filteredEvents} 
              loading={loading}
              onViewDetails={handleViewEventDetails}
            />
          </CardContent>
        </Card>
        
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Protocol Distribution</CardTitle>
            <CardDescription>Network traffic by protocol</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dashboardData.protocolData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {dashboardData.protocolData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          [
                            "#8884d8",
                            "#82ca9d",
                            "#ffc658",
                            "#ff8042",
                            "#0088FE",
                          ][index % 5]
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="mt-6 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-[#8884d8] mr-2"></div>
                  <span className="text-sm">HTTP</span>
                </div>
                <span className="text-sm font-medium">
                  {dashboardData.protocolData.find(p => p.name === 'HTTP')?.value || 0}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-[#82ca9d] mr-2"></div>
                  <span className="text-sm">HTTPS</span>
                </div>
                <span className="text-sm font-medium">
                  {dashboardData.protocolData.find(p => p.name === 'HTTPS')?.value || 0}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-[#ffc658] mr-2"></div>
                  <span className="text-sm">SSH</span>
                </div>
                <span className="text-sm font-medium">
                  {dashboardData.protocolData.find(p => p.name === 'SSH')?.value || 0}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-[#ff8042] mr-2"></div>
                  <span className="text-sm">FTP</span>
                </div>
                <span className="text-sm font-medium">
                  {dashboardData.protocolData.find(p => p.name === 'FTP')?.value || 0}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-3 w-3 rounded-full bg-[#0088FE] mr-2"></div>
                  <span className="text-sm">DNS</span>
                </div>
                <span className="text-sm font-medium">
                  {dashboardData.protocolData.find(p => p.name === 'DNS')?.value || 0}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
