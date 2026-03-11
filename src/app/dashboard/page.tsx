'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LayoutDashboard, RefreshCw, Download, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MetricsCards } from '@/components/dashboard/MetricsCards';
import { TrafficChart } from '@/components/dashboard/TrafficChart';
import { SecurityEvents } from '@/components/dashboard/SecurityEvents';
import { mockAPI } from '@/lib/mockData';

// Mock API calls
const fetchDashboardData = async () => {
  const [metrics, traffic, events] = await Promise.all([
    mockAPI.getMetrics(),
    mockAPI.getTraffic(),
    mockAPI.getSecurityEvents(),
  ]);

  return {
    metrics: metrics.data,
    traffic: traffic.data,
    events: events.data,
  };
};

export default function DashboardPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const { 
    data, 
    isLoading, 
    refetch, 
    isRefetching 
  } = useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboardData,
    refetchOnWindowFocus: false,
  });

  // Auto-refresh every 5 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      refetch();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [refetch]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setIsRefreshing(false);
  };

  const handleExport = (format: 'pdf' | 'csv') => {
    console.log(`Exporting dashboard data as ${format}`);
    alert(`Exporting dashboard data as ${format}...`);
  };

  const handleViewEventDetails = (event: any) => {
    console.log('Viewing event details:', event);
    alert(`Viewing details for event: ${event.id}\n${event.description}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your security status and network activity
          </p>
        </div>
        <div className="flex items-center space-x-2 mt-4 md:mt-0">
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2"
            onClick={handleRefresh}
            disabled={isRefreshing || isRefetching}
          >
            <RefreshCw className={`h-4 w-4 ${(isRefreshing || isRefetching) ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            className="gap-2"
            onClick={() => handleExport('pdf')}
          >
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      <div className="grid gap-4">
        <MetricsCards 
          metrics={data?.metrics} 
          loading={isLoading || isRefreshing || isRefetching} 
        />
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="threats">Threats</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Card className="col-span-4">
              <CardHeader>
                <CardTitle>Network Traffic</CardTitle>
              </CardHeader>
              <CardContent className="pl-2">
                <TrafficChart 
                  data={data?.traffic} 
                  loading={isLoading || isRefreshing || isRefetching} 
                />
              </CardContent>
            </Card>
            
            <Card className="col-span-3">
              <CardHeader>
                <CardTitle>Recent Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {isLoading || isRefreshing || isRefetching ? (
                    <div className="space-y-2">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-start space-x-3">
                          <div className="h-2 w-2 mt-1.5 rounded-full bg-gray-200" />
                          <div className="space-y-1">
                            <div className="h-4 w-48 bg-gray-200 rounded" />
                            <div className="h-3 w-32 bg-gray-100 rounded" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    data?.events.slice(0, 5).map((event: any) => (
                      <div key={event.id} className="flex items-start space-x-3">
                        <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-500 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium">{event.description}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(event.timestamp).toLocaleTimeString()} • {event.source}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="threats" className="space-y-4">
          <SecurityEvents 
            events={data?.events || []} 
            loading={isLoading || isRefreshing || isRefetching}
            onViewDetails={handleViewEventDetails}
          />
        </TabsContent>

        <TabsContent value="reports">
          <Card>
            <CardHeader>
              <CardTitle>Reports</CardTitle>
              <p className="text-sm text-muted-foreground">
                Generate and download security reports
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium">Daily Security Report</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Summary of security events and metrics for the day
                  </p>
                  <Button size="sm" onClick={() => handleExport('pdf')}>
                    <Download className="mr-2 h-4 w-4" />
                    Download PDF
                  </Button>
                </div>
                
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium">Threat Analysis</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Detailed analysis of security threats and vulnerabilities
                  </p>
                  <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
                    <Download className="mr-2 h-4 w-4" />
                    Export as CSV
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
