'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  ExternalLink, 
  Clock, 
  User, 
  Sparkles,
  Tag,
  Loader2,
  Brain,
  AlertTriangle,
  CheckCircle2,
  FileText
} from 'lucide-react'
import { explainArticle, summarizeArticle } from '@/lib/api'
import type { DisplayArticle } from '@/lib/types'

interface ArticleDetailProps {
  article: DisplayArticle | null
}

export function ArticleDetail({ article }: ArticleDetailProps) {
  const [explanation, setExplanation] = useState<string | null>(null)
  const [summary, setSummary] = useState<string | null>(null)
  const [isExplainLoading, setIsExplainLoading] = useState(false)
  const [isSummaryLoading, setIsSummaryLoading] = useState(false)
  const [explainError, setExplainError] = useState<string | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [explainMeta, setExplainMeta] = useState<{ model: string; tokens: number } | null>(null)
  const [summaryMeta, setSummaryMeta] = useState<{ model: string; tokens: number } | null>(null)

  const handleExplain = async () => {
    if (!article) return
    
    setIsExplainLoading(true)
    setExplainError(null)
    
    try {
      const result = await explainArticle({
        title: article.title,
        content: article.content || article.summary,
        label: article.classification === 'FAKE' ? 'Fake' : 'Real',
        confidence: article.confidence,
        source: article.source,
      })
      
      setExplanation(result.text)
      setExplainMeta({ model: result.model, tokens: result.tokens_used })
    } catch (err: any) {
      setExplainError(err.message || 'Failed to get explanation. Make sure the API server and OpenAI key are configured.')
    } finally {
      setIsExplainLoading(false)
    }
  }

  const handleSummarize = async () => {
    if (!article) return
    
    setIsSummaryLoading(true)
    setSummaryError(null)
    
    try {
      const result = await summarizeArticle({
        title: article.title,
        content: article.content || article.summary,
        label: article.classification === 'FAKE' ? 'Fake' : 'Real',
        confidence: article.confidence,
        source: article.source,
      })
      
      setSummary(result.text)
      setSummaryMeta({ model: result.model, tokens: result.tokens_used })
    } catch (err: any) {
      setSummaryError(err.message || 'Failed to get summary.')
    } finally {
      setIsSummaryLoading(false)
    }
  }

  if (!article) {
    return (
      <Card className="bg-card border-border h-full flex items-center justify-center">
        <CardContent className="text-center py-12">
          <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mx-auto mb-4">
            <Sparkles className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium text-foreground mb-2">Select an Article</h3>
          <p className="text-sm text-muted-foreground max-w-[250px]">
            Click on any article from the feed to view details and request an AI explanation
          </p>
        </CardContent>
      </Card>
    )
  }

  const formatDateTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  return (
    <Card className="bg-card border-border h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between mb-3">
          <Badge 
            variant={article.classification === 'FAKE' ? 'destructive' : 'default'}
            className={`text-sm font-semibold px-3 py-1 ${
              article.classification === 'FAKE' 
                ? 'bg-destructive/20 text-destructive border-destructive/30' 
                : 'bg-primary/20 text-primary border-primary/30'
            }`}
          >
            {article.classification === 'FAKE' ? (
              <AlertTriangle className="h-4 w-4 mr-1" />
            ) : (
              <CheckCircle2 className="h-4 w-4 mr-1" />
            )}
            {article.classification}
          </Badge>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Confidence</span>
            <div className="flex items-center gap-1">
              <div className="w-20 h-2 bg-secondary rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full ${
                    article.classification === 'FAKE' ? 'bg-destructive' : 'bg-primary'
                  }`}
                  style={{ width: `${article.confidence * 100}%` }}
                />
              </div>
              <span className="text-sm font-mono font-bold text-foreground">
                {(article.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
        <CardTitle className="text-xl leading-tight text-balance">{article.title}</CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col">
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground mb-4">
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {formatDateTime(article.publishedAt)}
          </span>
          {article.author && (
            <span className="flex items-center gap-1">
              <User className="h-4 w-4" />
              {article.author}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Tag className="h-4 w-4" />
            {article.category}
          </span>
          <Badge variant="outline">{article.source}</Badge>
        </div>

        <div className="bg-secondary/50 rounded-lg p-4 mb-4">
          <h4 className="text-xs uppercase tracking-wide text-muted-foreground font-medium mb-2">Content</h4>
          <p className="text-sm text-foreground leading-relaxed">
            {article.content || article.summary || 'No content available'}
          </p>
        </div>

        {/* GPT Actions */}
        <div className="flex gap-2 mb-4">
          <Button
            onClick={handleExplain}
            disabled={isExplainLoading}
            className="flex-1"
            variant={explanation ? 'outline' : 'default'}
          >
            {isExplainLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Brain className="h-4 w-4 mr-2" />
                {explanation ? 'Refresh Explanation' : 'Explain with GPT'}
              </>
            )}
          </Button>
          <Button
            onClick={handleSummarize}
            disabled={isSummaryLoading}
            variant="outline"
            className="flex-1"
          >
            {isSummaryLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Summarizing...
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 mr-2" />
                {summary ? 'Refresh Summary' : 'Summarize with GPT'}
              </>
            )}
          </Button>
          <Button variant="outline" size="icon" asChild>
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>
        </div>

        {/* Explanation Error */}
        {explainError && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 mb-4">
            <p className="text-xs text-destructive">{explainError}</p>
          </div>
        )}

        {/* GPT Explanation */}
        {explanation && (
          <div className="border border-border rounded-lg overflow-hidden mb-4">
            <div className="bg-secondary/50 px-4 py-2 border-b border-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">GPT Explanation</span>
                </div>
                {explainMeta && (
                  <span className="text-[10px] text-muted-foreground">
                    {explainMeta.model} · {explainMeta.tokens} tokens
                  </span>
                )}
              </div>
            </div>
            <ScrollArea className="max-h-[200px]">
              <div className="p-4 prose prose-sm dark:prose-invert max-w-none">
                {explanation.split('\n').map((line, i) => {
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return <h4 key={i} className="font-bold text-foreground mt-3 first:mt-0">{line.replace(/\*\*/g, '')}</h4>
                  }
                  if (line.match(/^\d\./)) {
                    return <p key={i} className="text-sm text-muted-foreground my-1 pl-4">{line}</p>
                  }
                  if (line.trim() === '') return <br key={i} />
                  return <p key={i} className="text-sm text-muted-foreground my-1">{line}</p>
                })}
              </div>
            </ScrollArea>
          </div>
        )}

        {/* Summary Error */}
        {summaryError && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 mb-4">
            <p className="text-xs text-destructive">{summaryError}</p>
          </div>
        )}

        {/* GPT Summary */}
        {summary && (
          <div className="border border-border rounded-lg overflow-hidden mb-4">
            <div className="bg-secondary/50 px-4 py-2 border-b border-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">GPT Summary</span>
                </div>
                {summaryMeta && (
                  <span className="text-[10px] text-muted-foreground">
                    {summaryMeta.model} · {summaryMeta.tokens} tokens
                  </span>
                )}
              </div>
            </div>
            <div className="p-4">
              <p className="text-sm text-foreground leading-relaxed">{summary}</p>
            </div>
          </div>
        )}

        <Separator className="my-4" />
        
        <div className="text-xs text-muted-foreground">
          <span className="font-medium">Processed:</span> {formatDateTime(article.processedAt)}
          <span className="mx-2">•</span>
          <span className="font-medium">Article ID:</span> {article.id}
        </div>
      </CardContent>
    </Card>
  )
}
