'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts'
import type { SystemStats, TimelineEntry } from '@/lib/types'

interface AnalyticsChartsProps {
  stats: SystemStats | undefined
  timeline: TimelineEntry[] | undefined
  isLoading: boolean
  error: any
}

// Color configuration aligned with system palette
const CHART_COLORS = {
  real: '#3B82F6',
  fake: '#EF4444',
  grid: '#E5E7EB',
  axis: '#6B7280',
  background: '#FFFFFF',
  border: '#E5E7EB',
  text: '#111827'
}

export function AnalyticsCharts({ stats, timeline, isLoading, error }: AnalyticsChartsProps) {
  const colors = CHART_COLORS

  // Build pie data from real stats
  const pieData = stats ? [
    { name: 'Real News', value: stats.real_pct, color: colors.real },
    { name: 'Fake News', value: stats.fake_pct, color: colors.fake }
  ] : []

  // Build per-source Real vs Fake bar chart data from source_breakdown
  const sourceChartData = (stats?.source_breakdown || []).map(s => ({
    category: s.source.length > 20 ? s.source.slice(0, 20) + '...' : s.source,
    real: s.real,
    fake: s.fake,
    total: s.total,
  })).slice(0, 7)

  // Source distribution from top_sources
  const sourceDistribution = (stats?.top_sources || []).map(s => ({
    source: s.source.length > 25 ? s.source.slice(0, 25) + '...' : s.source,
    count: s.count,
    fakeRate: stats?.fake_rate_by_source?.find(fr => fr.source === s.source)?.fake_rate
      ? (stats.fake_rate_by_source.find(fr => fr.source === s.source)!.fake_rate * 100)
      : 0,
  })).slice(0, 5)

  // Format timeline hours for display
  const formattedTimeline = (timeline || []).map(t => ({
    ...t,
    hour: t.hour.split('T')[1] || t.hour,
  }))

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground mb-1">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-xs text-muted-foreground">
              <span style={{ color: entry.color }}>{entry.name}:</span> {entry.value}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  // Loading state
  if (isLoading && !stats) {
    return (
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className={`bg-card border-border ${i === 0 || i === 2 ? 'xl:col-span-2' : ''}`}>
            <CardHeader className="pb-2">
              <Skeleton className="h-5 w-40" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-[250px] w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
      {/* Hourly Trend Chart */}
      <Card className="bg-card border-border xl:col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Articles Processed (24h)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            {formattedTimeline.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={formattedTimeline}>
                  <defs>
                    <linearGradient id="colorReal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors.real} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={colors.real} stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorFake" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors.fake} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={colors.fake} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                  <XAxis 
                    dataKey="hour" 
                    stroke={colors.axis}
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis 
                    stroke={colors.axis}
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="real"
                    name="Real"
                    stackId="1"
                    stroke={colors.real}
                    fill="url(#colorReal)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="fake"
                    name="Fake"
                    stackId="1"
                    stroke={colors.fake}
                    fill="url(#colorFake)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm text-muted-foreground">No timeline data available yet. Waiting for articles to be processed...</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Classification Distribution Pie */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Classification Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            {pieData.length > 0 && stats && stats.total > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => [`${value}%`, '']}
                    contentStyle={{
                      backgroundColor: colors.background,
                      border: `1px solid ${colors.border}`,
                      borderRadius: '8px',
                      color: colors.text
                    }}
                  />
                  <Legend 
                    verticalAlign="bottom"
                    formatter={(value) => <span style={{ color: colors.text, fontSize: '12px' }}>{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm text-muted-foreground">No classification data yet</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Source Classification Breakdown */}
      <Card className="bg-card border-border xl:col-span-2">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Classification by Source</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            {sourceChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceChartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} horizontal={false} />
                  <XAxis 
                    type="number"
                    stroke={colors.axis}
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis 
                    type="category"
                    dataKey="category"
                    stroke={colors.axis}
                    fontSize={11}
                    tickLine={false}
                    axisLine={false}
                    width={120}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="real" name="Real" fill={colors.real} stackId="a" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="fake" name="Fake" fill={colors.fake} stackId="a" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-sm text-muted-foreground">No source data available yet</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Source Analysis */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Source Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sourceDistribution.length > 0 ? (
              sourceDistribution.map((source) => (
                <div key={source.source} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-foreground">{source.source}</span>
                    <span className="text-xs text-muted-foreground">{source.count.toLocaleString()} articles</span>
                  </div>
                  <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
                    <div 
                      className="absolute inset-y-0 left-0 bg-primary rounded-full"
                      style={{ width: `${100 - source.fakeRate}%` }}
                    />
                    <div 
                      className="absolute inset-y-0 right-0 bg-destructive rounded-full"
                      style={{ width: `${source.fakeRate}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-primary">{(100 - source.fakeRate).toFixed(1)}% Real</span>
                    <span className="text-destructive">{source.fakeRate.toFixed(1)}% Fake</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-20">
                <p className="text-sm text-muted-foreground">No source data yet</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
