'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  ExternalLink, 
  Clock, 
  User, 
  Sparkles,
  Filter,
  RefreshCw,
  WifiOff,
  Wifi
} from 'lucide-react'
import type { DisplayArticle } from '@/lib/types'

interface ArticleFeedProps {
  articles: DisplayArticle[]
  onSelectArticle: (article: DisplayArticle) => void
  selectedArticleId: string | null
  totalArticles: number
  isLoading: boolean
  error: any
  isConnected: boolean
  onRefresh: () => void
}

export function ArticleFeed({ 
  articles, 
  onSelectArticle, 
  selectedArticleId,
  totalArticles,
  isLoading,
  error,
  isConnected,
  onRefresh,
}: ArticleFeedProps) {
  const [filter, setFilter] = useState<'all' | 'fake' | 'real'>('all')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const filteredArticles = articles.filter(article => {
    if (filter === 'all') return true
    return article.classification.toLowerCase() === filter
  })

  const handleRefresh = () => {
    setIsRefreshing(true)
    onRefresh()
    setTimeout(() => setIsRefreshing(false), 1000)
  }

  const formatTime = (dateString: string) => {
    if (!mounted || !dateString) return '--:--'
    try {
      const date = new Date(dateString)
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit'
      })
    } catch {
      return '--:--'
    }
  }

  // Loading state
  if (isLoading && articles.length === 0) {
    return (
      <Card className="bg-card border-border h-full flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Skeleton className="h-2 w-2 rounded-full" />
            <Skeleton className="h-5 w-32" />
          </div>
        </CardHeader>
        <CardContent className="flex-1 p-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="p-3 rounded-lg border border-border bg-secondary/50">
              <Skeleton className="h-4 w-16 mb-2" />
              <Skeleton className="h-4 w-full mb-1" />
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-32" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="bg-card border-border h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-primary animate-pulse' : 'bg-destructive'}`} />
            <CardTitle className="text-lg">Live Article Feed</CardTitle>
            <Badge variant="outline" className="text-[10px] h-5 font-mono">
              {totalArticles.toLocaleString()}
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            {isConnected ? (
              <Wifi className="h-3 w-3 text-primary" />
            ) : (
              <WifiOff className="h-3 w-3 text-destructive" />
            )}
            <Button 
              variant="ghost" 
              size="icon"
              onClick={handleRefresh}
              className="h-8 w-8"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-2">
          <Filter className="h-3 w-3 text-muted-foreground" />
          <div className="flex gap-1">
            {(['all', 'fake', 'real'] as const).map((f) => (
              <Button
                key={f}
                variant={filter === f ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilter(f)}
                className="h-7 px-3 text-xs capitalize"
              >
                {f}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0">
        <ScrollArea className="h-[500px]">
          <div className="space-y-2 p-4 pt-0">
            {error && articles.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <WifiOff className="h-8 w-8 text-destructive mb-3" />
                <p className="text-sm font-medium text-foreground mb-1">Cannot reach API</p>
                <p className="text-xs text-muted-foreground text-center">
                  Make sure the backend is running and try refreshing
                </p>
                <Button variant="outline" size="sm" className="mt-3" onClick={handleRefresh}>
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Retry
                </Button>
              </div>
            ) : filteredArticles.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Sparkles className="h-8 w-8 text-muted-foreground mb-3" />
                <p className="text-sm text-muted-foreground">
                  {filter === 'all' ? 'No articles yet. Waiting for the pipeline...' : `No ${filter} articles found`}
                </p>
              </div>
            ) : (
              filteredArticles.map((article, index) => (
                <button
                  key={article.id}
                  onClick={() => onSelectArticle(article)}
                  className={`w-full text-left p-3 rounded-lg border transition-all duration-200 animate-slide-up ${
                    selectedArticleId === article.id
                      ? 'bg-secondary border-primary/50'
                      : 'bg-secondary/50 border-border hover:bg-secondary hover:border-border'
                  }`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge 
                      variant={article.classification === 'FAKE' ? 'destructive' : 'default'}
                      className={`text-xs font-semibold ${
                        article.classification === 'FAKE' 
                          ? 'bg-destructive/20 text-destructive border-destructive/30' 
                          : 'bg-primary/20 text-primary border-primary/30'
                      }`}
                    >
                      {article.classification}
                    </Badge>
                    <span className="text-xs font-mono text-muted-foreground">
                      {(article.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  <h4 className="text-sm font-medium text-foreground line-clamp-2 mb-2">
                    {article.title}
                  </h4>
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatTime(article.processedAt)}
                      </span>
                      {article.author && (
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          <span className="truncate max-w-[80px]">{article.author}</span>
                        </span>
                      )}
                    </div>
                    <Badge variant="outline" className="text-[10px] h-5">
                      {article.source.length > 15 ? article.source.slice(0, 15) + '...' : article.source}
                    </Badge>
                  </div>
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
