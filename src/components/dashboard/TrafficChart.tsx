import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Area, AreaChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line } from 'recharts';
import { Skeleton } from '@/components/ui/skeleton';

interface TrafficDataPoint {
  timestamp: string;
  incoming: number;
  outgoing: number;
  threats: number;
  anomalies: number[];
}

interface TrafficChartProps {
  data?: TrafficDataPoint[];
  loading?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-medium">{label}</p>
        <p className="text-sm text-indigo-600">
          Incoming: <span className="font-medium">{payload[0].value} MB</span>
        </p>
        <p className="text-sm text-rose-600">
          Outgoing: <span className="font-medium">{payload[1].value} MB</span>
        </p>
        <p className="text-sm text-amber-600">
          Threats: <span className="font-medium">{payload[2].value}</span>
        </p>
      </div>
    );
  }
  return null;
};

export function TrafficChart({ data = [], loading = false }: TrafficChartProps) {
  if (loading) {
    return (
      <Card className="h-[400px] w-full">
        <CardHeader>
          <Skeleton className="h-6 w-48 mb-2" />
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  // If no data, show empty state
  if (data.length === 0) {
    return (
      <Card className="h-[400px] w-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">No traffic data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="h-[400px] w-full">
      <CardHeader>
        <CardTitle>Network Traffic</CardTitle>
        <p className="text-sm text-gray-500">Last 24 hours activity</p>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorIncoming" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorOutgoing" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#e11d48" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#e11d48" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#d97706" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#d97706" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis 
                dataKey="timestamp" 
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis 
                yAxisId="left" 
                orientation="left" 
                stroke="#6b7280" 
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <YAxis 
                yAxisId="right" 
                orientation="right" 
                stroke="#d97706" 
                tickLine={false}
                axisLine={false}
                tickMargin={10}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="incoming"
                stroke="#4f46e5"
                fillOpacity={1}
                fill="url(#colorIncoming)"
                name="Incoming (MB)"
              />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="outgoing"
                stroke="#e11d48"
                fillOpacity={1}
                fill="url(#colorOutgoing)"
                name="Outgoing (MB)"
              />
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="threats"
                stroke="#d97706"
                fillOpacity={1}
                fill="url(#colorThreats)"
                name="Threats"
              />
              {data.some(d => d.anomalies && d.anomalies.length > 0) && (
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="anomalies"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  name="Anomalies"
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
