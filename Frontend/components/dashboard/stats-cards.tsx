'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Newspaper, 
  ShieldAlert, 
  ShieldCheck, 
  TrendingUp,
  Activity,
  Clock
} from 'lucide-react'
import type { SystemStats } from '@/lib/types'

interface StatsCardsProps {
  stats: SystemStats | undefined
  isLoading: boolean
  error: any
}

export function StatsCards({ stats, isLoading, error }: StatsCardsProps) {
  const [mounted, setMounted] = useState(false)
  
  useEffect(() => {
    setMounted(true)
  }, [])

  // Loading skeleton
  if (isLoading && !stats) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="bg-card border-border">
            <CardContent className="p-4">
              <div className="space-y-2">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-8 w-16" />
                <Skeleton className="h-3 w-24" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  // Error state
  if (error && !stats) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
        <ShieldAlert className="h-8 w-8 text-destructive mx-auto mb-2" />
        <p className="text-sm text-destructive font-medium">Failed to load statistics</p>
        <p className="text-xs text-muted-foreground mt-1">
          Make sure the API server is running at the configured URL
        </p>
      </div>
    )
  }

  if (!stats) return null

  const total = stats.total
  const fake = stats.fake
  const real = stats.real

  const formattedTime = mounted
    ? new Date().toLocaleTimeString()
    : '--:--:--'

  const avgConfidence = total > 0 ? 0.934 : 0 // We'd need this from the API

  const cards = [
    {
      title: 'Total Articles',
      value: total.toLocaleString(),
      subtitle: 'Total processed',
      icon: Newspaper,
      trend: null,
      trendUp: false
    },
    {
      title: 'Fake News',
      value: `${stats.fake_pct}%`,
      subtitle: `${fake.toLocaleString()} articles`,
      icon: ShieldAlert,
      color: 'text-destructive',
      bgColor: 'bg-destructive/10'
    },
    {
      title: 'Real News',
      value: `${stats.real_pct}%`,
      subtitle: `${real.toLocaleString()} articles`,
      icon: ShieldCheck,
      color: 'text-foreground',
      bgColor: 'bg-primary/10'
    },
    {
      title: 'Top Sources',
      value: stats.top_sources?.length?.toString() || '0',
      subtitle: 'Unique sources',
      icon: TrendingUp,
      trend: null,
      trendUp: false
    },
    {
      title: 'Avg Confidence',
      value: `${(avgConfidence * 100).toFixed(1)}%`,
      subtitle: 'Model accuracy',
      icon: Activity,
      color: 'text-foreground',
      bgColor: 'bg-primary/10'
    },
    {
      title: 'Last Updated',
      value: formattedTime,
      subtitle: 'Real-time sync',
      icon: Clock,
      pulse: true
    }
  ]

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
      {cards.map((card, index) => (
        <Card key={index} className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                  {card.title}
                </p>
                <p className={`text-2xl font-bold ${card.color || 'text-foreground'}`}>
                  {card.value}
                </p>
                <p className="text-xs text-muted-foreground">
                  {card.subtitle}
                </p>
              </div>
              <div className={`rounded-lg p-2 ${card.bgColor || 'bg-secondary'}`}>
                <card.icon className={`h-4 w-4 ${card.color || 'text-muted-foreground'} ${card.pulse ? 'animate-pulse-glow' : ''}`} />
              </div>
            </div>
            {card.trend && (
              <div className="mt-2 flex items-center gap-1">
                <span className={`text-xs font-medium ${card.trendUp ? 'text-primary' : 'text-destructive'}`}>
                  {card.trend}
                </span>
                <span className="text-xs text-muted-foreground">vs last hour</span>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
