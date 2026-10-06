import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { APILog } from './types';
import { getStatusColor, getMethodColor } from './utils';

interface LogsTableProps {
  logs: APILog[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filterStatus: string;
  setFilterStatus: (status: string) => void;
  filterSource: string;
  setFilterSource: (source: string) => void;
  onLogClick: (log: APILog) => void;
}

export const LogsTable = ({
  logs,
  searchQuery,
  setSearchQuery,
  filterStatus,
  setFilterStatus,
  filterSource,
  setFilterSource,
  onLogClick,
}: LogsTableProps) => {
  const filteredLogs = logs.filter(log => {
    const requestBody = JSON.stringify(log.request.body || {}).toLowerCase();
    const matchesSearch = log.endpoint.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         log.method.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         requestBody.includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'success' && log.status >= 200 && log.status < 300) ||
                         (filterStatus === 'error' && log.status >= 400);
    const matchesSource = filterSource === 'all' || log.source === filterSource;
    
    return matchesSearch && matchesStatus && matchesSource;
  });

  return (
    <Card className="border-border bg-card">
      <div className="p-6 border-b border-border">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search logs... (endpoint, method, INN, receipt data)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-background border-border"
            />
          </div>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-full md:w-[180px] bg-background border-border">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="success">Success (2xx)</SelectItem>
              <SelectItem value="error">Errors (4xx, 5xx)</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterSource} onValueChange={setFilterSource}>
            <SelectTrigger className="w-full md:w-[180px] bg-background border-border">
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              <SelectItem value="bitrix">Bitrix24</SelectItem>
              <SelectItem value="ecomkassa">Payti</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" className="gap-2">
            <Icon name="Download" size={16} />
            Export
          </Button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b border-border bg-muted/30">
            <tr className="text-xs uppercase tracking-wider text-muted-foreground">
              <th className="text-left p-4 font-medium">Timestamp</th>
              <th className="text-left p-4 font-medium">Method</th>
              <th className="text-left p-4 font-medium">Endpoint</th>
              <th className="text-left p-4 font-medium">Status</th>
              <th className="text-left p-4 font-medium">Duration</th>
              <th className="text-left p-4 font-medium">Size</th>
              <th className="text-left p-4 font-medium">Source</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.map((log, index) => (
              <tr 
                key={log.id} 
                className="border-b border-border hover:bg-muted/20 transition-colors animate-fade-in cursor-pointer"
                style={{ animationDelay: `${index * 50}ms` }}
                onClick={() => onLogClick(log)}
              >
                <td className="p-4 text-sm text-muted-foreground font-mono">{log.timestamp}</td>
                <td className="p-4">
                  <Badge variant="outline" className={getMethodColor(log.method)}>
                    {log.method}
                  </Badge>
                </td>
                <td className="p-4 text-sm font-mono">{log.endpoint}</td>
                <td className="p-4">
                  <span className={`font-bold ${getStatusColor(log.status)}`}>
                    {log.status}
                  </span>
                </td>
                <td className="p-4 text-sm text-muted-foreground">{log.duration}ms</td>
                <td className="p-4 text-sm text-muted-foreground">{log.size}</td>
                <td className="p-4">
                  <Badge variant="outline" className="capitalize">
                    {log.source}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredLogs.length === 0 && (
        <div className="p-12 text-center text-muted-foreground">
          <Icon name="Search" size={48} className="mx-auto mb-4 opacity-50" />
          <p>No logs found matching your filters</p>
        </div>
      )}
    </Card>
  );
};