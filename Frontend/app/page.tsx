'use client'

import { useState, useCallback } from 'react'
import { Header } from '@/components/dashboard/header'
import { SidebarNav } from '@/components/dashboard/sidebar-nav'
import { StatsCards } from '@/components/dashboard/stats-cards'
import { ArticleFeed } from '@/components/dashboard/article-feed'
import { ArticleDetail } from '@/components/dashboard/article-detail'
import { AnalyticsCharts } from '@/components/dashboard/analytics-charts'
import { SystemArchitecture } from '@/components/dashboard/system-architecture'
import { LiveIndicator } from '@/components/dashboard/live-indicator'
import { useStats, useTimeline, useArticles } from '@/hooks/use-api'
import { useWebSocket } from '@/hooks/use-websocket'
import { toDisplayArticle, type DisplayArticle, type Article } from '@/lib/types'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [selectedArticle, setSelectedArticle] = useState<DisplayArticle | null>(null)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [articleFilter, setArticleFilter] = useState<'all' | 'Fake' | 'Real'>('all')
  const [articlePage, setArticlePage] = useState(1)

  // ─── Real-time data hooks ───────────────────────────────────────────
  const { data: stats, error: statsError, isLoading: statsLoading } = useStats(10000)
  const { data: timeline, error: timelineError } = useTimeline(24, 30000)
  const { 
    data: articlesData, 
    error: articlesError, 
    isLoading: articlesLoading,
    mutate: mutateArticles 
  } = useArticles({ 
    label: articleFilter === 'all' ? 'all' : articleFilter, 
    page: articlePage, 
    page_size: 20 
  }, 8000)

  // ─── WebSocket for live article push ────────────────────────────────
  const handleNewArticles = useCallback((newArticles: Article[]) => {
    // Re-fetch articles list when new ones arrive via WS
    mutateArticles()
  }, [mutateArticles])

  const { isConnected, articleCount, lastSource } = useWebSocket({
    onNewArticles: handleNewArticles,
    enabled: true,
  })

  // ─── Map API articles to display format ─────────────────────────────
  const displayArticles: DisplayArticle[] = (articlesData?.articles || []).map(toDisplayArticle)
  const totalArticles = articlesData?.total || 0

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-2xl font-bold text-foreground">Dashboard</h2>
                <p className="text-sm text-muted-foreground">
                  Real-time monitoring of the fake news detection pipeline
                </p>
              </div>
              <LiveIndicator 
                isConnected={isConnected}
                articleCount={articleCount}
                lastSource={lastSource}
              />
            </div>
            
            <StatsCards 
              stats={stats}
              isLoading={statsLoading}
              error={statsError}
            />
            
            <AnalyticsCharts 
              stats={stats}
              timeline={timeline}
              isLoading={statsLoading}
              error={statsError || timelineError}
            />
          </div>
        )
      
      case 'articles':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-foreground">Article Library</h2>
              <p className="text-sm text-muted-foreground">
                Browse and analyze all processed articles
              </p>
            </div>
            
            <div className="grid gap-6 lg:grid-cols-2">
              <ArticleFeed 
                articles={displayArticles}
                onSelectArticle={setSelectedArticle}
                selectedArticleId={selectedArticle?.id ?? null}
                totalArticles={totalArticles}
                isLoading={articlesLoading}
                error={articlesError}
                isConnected={isConnected}
                onRefresh={() => mutateArticles()}
              />
              <ArticleDetail article={selectedArticle} />
            </div>
          </div>
        )
      
      case 'architecture':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-foreground">System Architecture</h2>
              <p className="text-sm text-muted-foreground">
                Understand how the TruthStream AI pipeline works
              </p>
            </div>
            
            <SystemArchitecture />
            
            {/* Data Flow - Full Width */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Data Flow</h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 border border-border/50">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center flex-shrink-0">1</span>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Ingestion</h4>
                    <p className="text-sm text-muted-foreground">News articles are fetched from NewsAPI and GNews every 60 seconds using scheduled jobs.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 border border-border/50">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center flex-shrink-0">2</span>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Streaming</h4>
                    <p className="text-sm text-muted-foreground">Raw articles are published to Apache Kafka topics for reliable message queuing.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 border border-border/50">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center flex-shrink-0">3</span>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Processing</h4>
                    <p className="text-sm text-muted-foreground">Spark Structured Streaming consumes messages, cleans text, and extracts features.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 border border-border/50">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center flex-shrink-0">4</span>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Classification</h4>
                    <p className="text-sm text-muted-foreground">The RoBERTa model analyzes each article and outputs a fake/real classification with confidence.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 border border-border/50">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center flex-shrink-0">5</span>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Storage</h4>
                    <p className="text-sm text-muted-foreground">Results are stored in MongoDB with full article metadata and classification details.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 border border-border/50">
                  <span className="h-8 w-8 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center flex-shrink-0">6</span>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">API</h4>
                    <p className="text-sm text-muted-foreground">FastAPI serves the data through RESTful endpoints for the frontend dashboard.</p>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Technology Stack - Full Width Below */}
            <div className="rounded-lg border border-border bg-card p-6">
              <h3 className="text-lg font-semibold text-foreground mb-6">Technology Stack</h3>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <div className="p-4 rounded-lg bg-chart-5/10 border border-chart-5/20">
                  <h4 className="text-xs font-semibold text-chart-5 uppercase tracking-wider mb-3">Data Sources</h4>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-chart-5"></span>
                      NewsAPI
                    </li>
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-chart-5"></span>
                      GNews
                    </li>
                  </ul>
                </div>
                <div className="p-4 rounded-lg bg-chart-4/10 border border-chart-4/20">
                  <h4 className="text-xs font-semibold text-chart-4 uppercase tracking-wider mb-3">Streaming</h4>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-chart-4"></span>
                      Apache Kafka
                    </li>
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-chart-4"></span>
                      Apache Spark
                    </li>
                  </ul>
                </div>
                <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                  <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-3">AI/ML</h4>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-primary"></span>
                      RoBERTa Model
                    </li>
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-primary"></span>
                      GPT-4 (Explanations)
                    </li>
                  </ul>
                </div>
                <div className="p-4 rounded-lg bg-chart-3/10 border border-chart-3/20">
                  <h4 className="text-xs font-semibold text-chart-3 uppercase tracking-wider mb-3">Backend</h4>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-chart-3"></span>
                      MongoDB
                    </li>
                    <li className="flex items-center gap-2 text-sm text-foreground">
                      <span className="h-2 w-2 rounded-full bg-chart-3"></span>
                      FastAPI
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )
      
      default:
        return (
          <div className="flex items-center justify-center h-[400px]">
            <div className="text-center">
              <h3 className="text-lg font-medium text-foreground mb-2">Coming Soon</h3>
              <p className="text-sm text-muted-foreground">This section is under development</p>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header 
        onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)} 
        menuOpen={mobileMenuOpen}
        isConnected={isConnected}
      />
      
      <div className="flex">
        {/* Desktop Sidebar */}
        <div className="hidden md:block w-64 flex-shrink-0">
          <div className="sticky top-16 h-[calc(100vh-4rem)]">
            <SidebarNav 
              activeTab={activeTab} 
              onTabChange={(tab) => {
                setActiveTab(tab)
                setSelectedArticle(null)
              }}
              totalArticles={stats?.total}
            />
          </div>
        </div>

        {/* Mobile Sidebar Overlay */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 md:hidden">
            <div 
              className="absolute inset-0 bg-background/80 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="absolute left-0 top-16 bottom-0 w-64">
              <SidebarNav 
                activeTab={activeTab} 
                onTabChange={(tab) => {
                  setActiveTab(tab)
                  setSelectedArticle(null)
                  setMobileMenuOpen(false)
                }}
                totalArticles={stats?.total}
              />
            </div>
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 overflow-auto">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}
