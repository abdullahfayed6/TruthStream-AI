'use client'

import { Badge } from '@/components/ui/badge'
import { Activity, Wifi, WifiOff } from 'lucide-react'

interface LiveIndicatorProps {
  isConnected: boolean
  articleCount: number
  lastSource: string | null
}

export function LiveIndicator({ isConnected, articleCount, lastSource }: LiveIndicatorProps) {
  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-secondary/50 rounded-lg border border-border">
      <div className="flex items-center gap-2">
        {isConnected ? (
          <>
            <Activity className="h-4 w-4 text-primary animate-pulse" />
            <span className="text-sm font-medium text-foreground">Live Stream</span>
          </>
        ) : (
          <>
            <WifiOff className="h-4 w-4 text-destructive" />
            <span className="text-sm font-medium text-muted-foreground">Connecting...</span>
          </>
        )}
      </div>
      {articleCount > 0 && (
        <Badge variant="outline" className="text-xs font-mono">
          +{articleCount} new
        </Badge>
      )}
      {lastSource && (
        <span className="text-xs text-muted-foreground hidden sm:inline">
          Last: <span className="text-foreground">{lastSource}</span>
        </span>
      )}
      <div className="flex items-center gap-1 ml-auto">
        {isConnected ? (
          <Wifi className="h-3 w-3 text-primary" />
        ) : (
          <WifiOff className="h-3 w-3 text-destructive" />
        )}
        <span className={`text-[10px] ${isConnected ? 'text-primary' : 'text-destructive'}`}>
          {isConnected ? 'LIVE' : 'OFFLINE'}
        </span>
      </div>
    </div>
  )
}
