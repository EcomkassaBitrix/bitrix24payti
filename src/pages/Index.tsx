import { useState } from 'react';
import Icon from '@/components/ui/icon';
import { MetricsCards } from '@/components/api-monitor/MetricsCards';
import { PerformanceCharts } from '@/components/api-monitor/PerformanceCharts';
import { LogsTable } from '@/components/api-monitor/LogsTable';
import { LogDetailsDialog } from '@/components/api-monitor/LogDetailsDialog';
import { mockLogs, performanceData, statusData } from '@/components/api-monitor/mockData';
import { APILog } from '@/components/api-monitor/types';

const Index = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSource, setFilterSource] = useState<string>('all');
  const [selectedLog, setSelectedLog] = useState<APILog | null>(null);

  return (
    <div className="min-h-screen bg-background p-6 console-text">
      <div className="max-w-[1600px] mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-success flex items-center gap-3">
              <Icon name="Terminal" size={32} />
              Payti API Monitor
            </h1>
            <p className="text-muted-foreground mt-1">Real-time API logging & analytics</p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse-glow" />
            <span>Live monitoring</span>
          </div>
        </div>

        <MetricsCards logs={mockLogs} />

        <PerformanceCharts performanceData={performanceData} statusData={statusData} />

        <LogsTable
          logs={mockLogs}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          filterStatus={filterStatus}
          setFilterStatus={setFilterStatus}
          filterSource={filterSource}
          setFilterSource={setFilterSource}
          onLogClick={setSelectedLog}
        />

        <LogDetailsDialog log={selectedLog} onClose={() => setSelectedLog(null)} />
      </div>
    </div>
  );
};

export default Index;
