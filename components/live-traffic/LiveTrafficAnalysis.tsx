'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { apiClient } from "@/lib/api-client";
import { Skeleton } from "@/components/ui/skeleton";

interface TrafficData {
  timestamp: string;
  bytes: number;
  packets: number;
  protocol: string;
  source_ip: string;
  destination_ip: string;
}

export function LiveTrafficAnalysis() {
  const [trafficData, setTrafficData] = useState<TrafficData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'protocols' | 'endpoints'>('overview');
  const [timeRange, setTimeRange] = useState('5m');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrafficData = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get(`/api/network/traffic?range=${timeRange}`);
        setTrafficData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching traffic data:', err);
        setError('Failed to load traffic data. Please try again later.');
        // Mock data for demo purposes
        setTrafficData(generateMockTrafficData());
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrafficData();
    const interval = setInterval(fetchTrafficData, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [timeRange]);

  // Helper function to generate mock data for demo
  const generateMockTrafficData = (): TrafficData[] => {
    const protocols = ['HTTP', 'HTTPS', 'DNS', 'SSH', 'RDP'];
    const data: TrafficData[] = [];
    const now = new Date();
    
    for (let i = 0; i < 20; i++) {
      const timestamp = new Date(now.getTime() - (20 - i) * 10000); // 10-second intervals
      data.push({
        timestamp: timestamp.toISOString(),
        bytes: Math.floor(Math.random() * 10000) + 1000,
        packets: Math.floor(Math.random() * 100) + 10,
        protocol: protocols[Math.floor(Math.random() * protocols.length)],
        source_ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
        destination_ip: `10.0.0.${Math.floor(Math.random() * 255)}`
      });
    }
    return data;
  };

  // Process data for charts
  const processChartData = () => {
    return trafficData.map(item => ({
      time: new Date(item.timestamp).toLocaleTimeString(),
      bytes: item.bytes,
      packets: item.packets
    }));
  };

  // Group by protocol
  const protocolStats = trafficData.reduce((acc, item) => {
    if (!acc[item.protocol]) {
      acc[item.protocol] = { count: 0, bytes: 0 };
    }
    acc[item.protocol].count += 1;
    acc[item.protocol].bytes += item.bytes;
    return acc;
  }, {} as Record<string, { count: number; bytes: number }>);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Live Network Traffic Analysis</h2>
        <div className="flex space-x-2">
          {['5m', '15m', '1h', '6h'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-sm rounded-md ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <span className="block sm:inline">{error}</span>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Traffic</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                `${(trafficData.reduce((sum, item) => sum + item.bytes, 0) / (1024 * 1024)).toFixed(2)} MB`
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {trafficData.length} packets analyzed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Packets/s</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? (
                <Skeleton className="h-8 w-24" />
              ) : trafficData.length > 1 ? (
                `${(trafficData.reduce((sum, item) => sum + item.packets, 0) / trafficData.length).toFixed(1)}/s`
              ) : (
                'N/A'
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {isLoading ? (
                <Skeleton className="h-4 w-32 mt-1" />
              ) : (
                `Peak: ${Math.max(...trafficData.map(item => item.packets))} packets`
              )}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Protocols</CardTitle>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              className="h-4 w-4 text-muted-foreground"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? (
                <Skeleton className="h-8 w-24" />
              ) : (
                Object.keys(protocolStats).length
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {isLoading ? (
                <Skeleton className="h-4 w-32 mt-1" />
              ) : (
                `Top: ${Object.entries(protocolStats).sort((a, b) => b[1].count - a[1].count)[0]?.[0] || 'N/A'}`
              )}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Traffic Volume</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {isLoading ? (
              <div className="h-full flex items-center justify-center">
                <div className="animate-pulse flex space-x-4 w-full h-full">
                  <div className="flex-1 space-y-4 py-1">
                    <div className="h-3/4 bg-gray-200 rounded w-full"></div>
                  </div>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={processChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="bytes" stroke="#8884d8" fill="#8884d8" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Packets Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-80">
            {isLoading ? (
              <div className="h-full flex items-center justify-center">
                <div className="animate-pulse flex space-x-4 w-full h-full">
                  <div className="flex-1 space-y-4 py-1">
                    <div className="h-3/4 bg-gray-200 rounded w-full"></div>
                  </div>
                </div>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={processChartData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="packets" stroke="#82ca9d" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Network Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source IP</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Destination IP</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Protocol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bytes</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Packets</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-500">
                      Loading traffic data...
                    </td>
                  </tr>
                ) : trafficData.length > 0 ? (
                  [...trafficData]
                    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
                    .slice(0, 10)
                    .map((item, index) => (
                      <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {item.source_ip}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {item.destination_ip}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                            {item.protocol}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {(item.bytes / 1024).toFixed(2)} KB
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {item.packets}
                        </td>
                      </tr>
                    ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-500">
                      No traffic data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
