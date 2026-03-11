import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AlertCircle, AlertTriangle, ShieldAlert, ShieldCheck, ShieldOff } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

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

interface SecurityEventsProps {
  events: SecurityEvent[]
  loading?: boolean
  onViewDetails?: (event: SecurityEvent) => void
}

const getSeverityIcon = (severity: ThreatLevel) => {
  switch (severity) {
    case 'critical':
      return <ShieldAlert className="h-4 w-4 text-red-500" />
    case 'high':
      return <AlertTriangle className="h-4 w-4 text-amber-500" />
    case 'medium':
      return <AlertCircle className="h-4 w-4 text-blue-500" />
    case 'low':
      return <ShieldCheck className="h-4 w-4 text-green-500" />
    default:
      return <ShieldOff className="h-4 w-4 text-gray-400" />
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'new':
      return <Badge variant="secondary">New</Badge>
    case 'investigating':
      return <Badge variant="warning">Investigating</Badge>
    case 'resolved':
      return <Badge variant="success">Resolved</Badge>
    default:
      return <Badge variant="outline">Unknown</Badge>
  }
}

export function SecurityEvents({ events, loading = false, onViewDetails }: SecurityEventsProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-center py-8">
        <ShieldCheck className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No security events</h3>
        <p className="mt-1 text-sm text-gray-500">Your network is currently secure with no active threats.</p>
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[50px]">Severity</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id} className="hover:bg-gray-50">
              <TableCell>
                <div className="flex items-center">
                  {getSeverityIcon(event.severity)}
                  <span className="ml-2 capitalize">{event.severity}</span>
                </div>
              </TableCell>
              <TableCell className="font-medium">{event.type}</TableCell>
              <TableCell className="font-mono text-sm">{event.source}</TableCell>
              <TableCell>
                <div className="text-sm text-gray-500">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
              </TableCell>
              <TableCell>{getStatusBadge(event.status)}</TableCell>
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
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
