import { AlertTriangle, Shield, Server, User, Network, Clock, Search } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

const priorityIcons = {
  high: <AlertTriangle className="h-4 w-4 text-red-500" />,
  medium: <AlertTriangle className="h-4 w-4 text-amber-500" />,
  low: <AlertTriangle className="h-4 w-4 text-blue-500" />,
};

const typeIcons = {
  threat: <Shield className="h-4 w-4 text-red-500" />,
  system: <Server className="h-4 w-4 text-blue-500" />,
  user: <User className="h-4 w-4 text-green-500" />,
  network: <Network className="h-4 w-4 text-purple-500" />,
};

interface SecurityEvent {
  id: string;
  timestamp: string;
  type: keyof typeof typeIcons;
  priority: 'high' | 'medium' | 'low';
  source: string;
  description: string;
  status: 'resolved' | 'investigating' | 'new';
}

interface SecurityEventsProps {
  events?: SecurityEvent[];
  loading?: boolean;
  onViewDetails?: (event: SecurityEvent) => void;
}

export function SecurityEvents({ events = [], loading = false, onViewDetails }: SecurityEventsProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  const filteredEvents = events
    .filter(event => {
      const matchesSearch = 
        event.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.description.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesFilter = filter === 'all' || event.priority === filter;
      
      return matchesSearch && matchesFilter;
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'resolved':
        return 'success';
      case 'investigating':
        return 'warning';
      case 'new':
      default:
        return 'destructive';
    }
  };

  const getPriorityVariant = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'warning';
      case 'low':
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-10 w-64" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <CardTitle>Security Events</CardTitle>
            <p className="text-sm text-gray-500 mt-1">Recent security-related events and alerts</p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search events..."
              className="pl-10 w-full md:w-64"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'high' ? 'destructive' : 'outline'}
            size="sm"
            onClick={() => setFilter('high')}
          >
            High
          </Button>
          <Button
            variant={filter === 'medium' ? 'warning' : 'outline'}
            size="sm"
            onClick={() => setFilter('medium')}
          >
            Medium
          </Button>
          <Button
            variant={filter === 'low' ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => setFilter('low')}
          >
            Low
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Type</TableHead>
                <TableHead>Event</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Time</TableHead>
                <TableHead className="w-[100px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEvents.length > 0 ? (
                filteredEvents.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>
                      <div className="flex items-center">
                        <span className="mr-2">{typeIcons[event.type]}</span>
                        {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">
                      <div className="line-clamp-1">{event.description}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-500">{event.source}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getPriorityVariant(event.priority)}>
                        {priorityIcons[event.priority]}
                        <span className="ml-1">{event.priority}</span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(event.status)}>
                        {event.status.charAt(0).toUpperCase() + event.status.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center text-sm text-gray-500">
                        <Clock className="mr-1 h-3.5 w-3.5" />
                        {new Date(event.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetails?.(event)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} className="h-24 text-center">
                    <div className="flex flex-col items-center justify-center py-6">
                      <Shield className="h-10 w-10 text-gray-300 mb-2" />
                      <p className="text-gray-500">No security events found</p>
                      {searchTerm && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2"
                          onClick={() => setSearchTerm('')}
                        >
                          Clear search
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
        {filteredEvents.length > 0 && (
          <div className="flex items-center justify-end space-x-2 mt-4">
            <Button variant="outline" size="sm">
              Previous
            </Button>
            <Button variant="outline" size="sm">
              Next
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
