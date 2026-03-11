import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Shield, AlertTriangle, HardDrive, ArrowUpDown } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
}

const MetricCard = ({ title, value, icon, trend, loading }: MetricCardProps) => {
  if (loading) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-16 mb-2" />
          <Skeleton className="h-4 w-20" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-gray-500">{title}</CardTitle>
          <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600">
            {icon}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <div className={`flex items-center text-sm mt-1 ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
            <ArrowUpDown 
              className={`h-4 w-4 mr-1 ${trend.isPositive ? 'rotate-0' : 'rotate-180'}`} 
            />
            {Math.abs(trend.value)}% from last week
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface MetricsCardsProps {
  metrics?: {
    securityScore: number;
    activeThreats: number;
    networkPerformance: number;
    devicesOnline: number;
  };
  loading?: boolean;
}

export function MetricsCards({ metrics, loading = false }: MetricsCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        title="Security Score"
        value={`${metrics?.securityScore || 0}%`}
        icon={<Shield className="h-4 w-4" />}
        trend={{ value: 12, isPositive: true }}
        loading={loading}
      />
      <MetricCard
        title="Active Threats"
        value={metrics?.activeThreats || 0}
        icon={<AlertTriangle className="h-4 w-4" />}
        trend={{ value: 5, isPositive: false }}
        loading={loading}
      />
      <MetricCard
        title="Network Performance"
        value={`${metrics?.networkPerformance || 0}%`}
        icon={<Activity className="h-4 w-4" />}
        trend={{ value: 2, isPositive: true }}
        loading={loading}
      />
      <MetricCard
        title="Devices Online"
        value={metrics?.devicesOnline || 0}
        icon={<HardDrive className="h-4 w-4" />}
        loading={loading}
      />
    </div>
  );
}
