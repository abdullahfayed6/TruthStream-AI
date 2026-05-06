'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Newspaper, 
  MessageSquare, 
  Zap, 
  Brain, 
  Database, 
  Server,
  ArrowRight,
  RefreshCw
} from 'lucide-react'

const pipelineSteps = [
  {
    id: 'sources',
    title: 'News Sources',
    description: 'NewsAPI & GNews',
    detail: 'Articles fetched every 60 seconds',
    icon: Newspaper,
    color: 'bg-chart-5/20 text-chart-5 border-chart-5/30'
  },
  {
    id: 'kafka',
    title: 'Apache Kafka',
    description: 'Message Queue',
    detail: 'Real-time event streaming',
    icon: MessageSquare,
    color: 'bg-chart-4/20 text-chart-4 border-chart-4/30'
  },
  {
    id: 'spark',
    title: 'Apache Spark',
    description: 'Structured Streaming',
    detail: 'Data processing & cleaning',
    icon: Zap,
    color: 'bg-chart-3/20 text-chart-3 border-chart-3/30'
  },
  {
    id: 'roberta',
    title: 'RoBERTa Model',
    description: 'AI Classification',
    detail: 'Fake/Real news detection',
    icon: Brain,
    color: 'bg-primary/20 text-primary border-primary/30'
  },
  {
    id: 'mongodb',
    title: 'MongoDB',
    description: 'Data Storage',
    detail: 'Classified articles stored',
    icon: Database,
    color: 'bg-chart-4/20 text-chart-4 border-chart-4/30'
  },
  {
    id: 'fastapi',
    title: 'FastAPI',
    description: 'REST Backend',
    detail: 'Serves data to frontend',
    icon: Server,
    color: 'bg-chart-5/20 text-chart-5 border-chart-5/30'
  }
]

export function SystemArchitecture() {
  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">System Architecture</CardTitle>
          <Badge variant="outline" className="text-xs">
            <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
            Live Pipeline
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Real-time big data pipeline for fake news detection
        </p>
      </CardHeader>
      <CardContent>
        {/* Desktop View */}
        <div className="hidden lg:flex items-center justify-between gap-2">
          {pipelineSteps.map((step, index) => (
            <div key={step.id} className="flex items-center">
              <div className="flex flex-col items-center text-center">
                <div className={`w-16 h-16 rounded-xl border ${step.color} flex items-center justify-center mb-3 transition-transform hover:scale-110`}>
                  <step.icon className="h-7 w-7" />
                </div>
                <h4 className="text-sm font-medium text-foreground mb-1">{step.title}</h4>
                <p className="text-xs text-muted-foreground mb-1">{step.description}</p>
                <p className="text-[10px] text-muted-foreground/70 max-w-[100px]">{step.detail}</p>
              </div>
              {index < pipelineSteps.length - 1 && (
                <ArrowRight className="h-5 w-5 text-muted-foreground mx-2 flex-shrink-0 animate-pulse" />
              )}
            </div>
          ))}
        </div>

        {/* Mobile View */}
        <div className="lg:hidden space-y-3">
          {pipelineSteps.map((step, index) => (
            <div key={step.id} className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-lg border ${step.color} flex items-center justify-center flex-shrink-0`}>
                <step.icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-medium text-foreground">{step.title}</h4>
                  <Badge variant="outline" className="text-[10px] h-5">{step.description}</Badge>
                </div>
                <p className="text-xs text-muted-foreground truncate">{step.detail}</p>
              </div>
              {index < pipelineSteps.length - 1 && (
                <ArrowRight className="h-4 w-4 text-muted-foreground rotate-90 lg:rotate-0" />
              )}
            </div>
          ))}
        </div>

        {/* Data Flow Summary */}
        <div className="mt-6 pt-4 border-t border-border">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">60s</p>
              <p className="text-xs text-muted-foreground">Fetch Interval</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">{"<"}2s</p>
              <p className="text-xs text-muted-foreground">Processing Time</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">93.4%</p>
              <p className="text-xs text-muted-foreground">Model Accuracy</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-foreground">24/7</p>
              <p className="text-xs text-muted-foreground">Uptime</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
