import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts"
import { Skeleton } from "@/components/ui/skeleton"

interface TrafficChartProps {
  data: Array<{
    time: string
    traffic: number
    threats: number
    anomalies: number
  }>
  loading?: boolean
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;
  
  const trafficValue = payload.find((p: any) => p.dataKey === 'traffic')?.value ?? 0;
  const threatsValue = payload.find((p: any) => p.dataKey === 'threats')?.value ?? 0;
  const anomaliesValue = payload.find((p: any) => p.dataKey === 'anomalies')?.value ?? 0;

  return (
    <div className="bg-white p-4 border rounded-lg shadow-lg">
      <p className="font-medium">{label}</p>
      <p className="text-sm text-blue-500">
        Traffic: <span className="font-mono">{trafficValue} req/s</span>
      </p>
      <p className="text-sm text-red-500">
        Threats: <span className="font-mono">{threatsValue}</span>
      </p>
      <p className="text-sm text-amber-500">
        Anomalies: <span className="font-mono">{anomaliesValue}</span>
      </p>
    </div>
  );
};

export function TrafficChart({ data, loading = false }: TrafficChartProps) {
  if (loading) {
    return (
      <Card className="col-span-4">
        <CardHeader>
          <CardTitle>Network Traffic</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="col-span-4">
      <CardHeader>
        <CardTitle>Network Traffic & Threats</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{
                top: 10,
                right: 30,
                left: 0,
                bottom: 0,
              }}
            >
              <defs>
                <linearGradient id="colorTraffic" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
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
                stroke="#3b82f6" 
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                yAxisId="right" 
                orientation="right" 
                stroke="#ef4444" 
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="traffic"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorTraffic)"
                name="Traffic"
              />
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="threats"
                stroke="#ef4444"
                fillOpacity={1}
                fill="url(#colorThreats)"
                name="Threats"
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="anomalies"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="Anomalies"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
