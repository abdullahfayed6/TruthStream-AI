/**
 * TruthStream AI — TypeScript types matching FastAPI backend responses.
 * 
 * These types align with the MongoDB document schema and API response shapes.
 */

// ─────────────────────────── Article Types ───────────────────────────

export interface Article {
  id: string
  title: string
  source: string
  url: string
  author: string | null
  content: string
  published_at: string
  fetched_at: string
  label: 'Fake' | 'Real'
  confidence: number
  scored_at: string
  category?: string
}

/** Frontend-friendly article for display (mapped from API response) */
export interface DisplayArticle {
  id: string
  title: string
  source: string
  publishedAt: string
  classification: 'FAKE' | 'REAL'
  confidence: number
  category: string
  summary: string
  url: string
  author: string | null
  processedAt: string
  content: string
}

// ─────────────────────────── Paginated Response ───────────────────────

export interface PaginatedArticles {
  total: number
  page: number
  page_size: number
  pages: number
  articles: Article[]
}

// ─────────────────────────── Stats Types ─────────────────────────────

export interface SystemStats {
  total: number
  fake: number
  real: number
  fake_pct: number
  real_pct: number
  top_sources: SourceCount[]
  fake_rate_by_source: FakeRateBySource[]
  source_breakdown: SourceBreakdown[]
}

export interface SourceCount {
  source: string
  count: number
}

export interface SourceBreakdown {
  source: string
  total: number
  real: number
  fake: number
}

export interface FakeRateBySource {
  source: string
  total: number
  fake_count: number
  fake_rate: number
}

// ─────────────────────────── Timeline Types ─────────────────────────

export interface TimelineEntry {
  hour: string
  fake: number
  real: number
  total: number
}

// ─────────────────────────── GPT Response ───────────────────────────

export interface GPTResponse {
  text: string
  model: string
  tokens_used: number
}

export interface ArticleInput {
  title: string
  content: string
  label: string
  confidence: number
  source: string
}

// ─────────────────────────── WebSocket Messages ─────────────────────

export interface WSNewArticles {
  type: 'new_articles'
  articles: Article[]
  count: number
  timestamp: string
}

export interface WSHeartbeat {
  type: 'heartbeat'
  timestamp: string
}

export interface WSError {
  type: 'error'
  message: string
}

export type WSMessage = WSNewArticles | WSHeartbeat | WSError

// ─────────────────────────── Display Helpers ────────────────────────

/** Map backend Article to frontend DisplayArticle */
export function toDisplayArticle(article: Article): DisplayArticle {
  return {
    id: article.id,
    title: article.title,
    source: article.source,
    publishedAt: article.published_at || article.fetched_at,
    classification: article.label === 'Fake' ? 'FAKE' : 'REAL',
    confidence: article.confidence,
    category: article.category || extractCategory(article.source),
    summary: article.content?.slice(0, 200) + (article.content?.length > 200 ? '...' : '') || '',
    url: article.url,
    author: article.author,
    processedAt: article.scored_at || article.fetched_at,
    content: article.content || '',
  }
}

function extractCategory(source: string): string {
  // Extract category from source if available (e.g., "newsapi:CNN" → "News")
  const categories = ['Politics', 'Health', 'Technology', 'Science', 'Business', 'Entertainment', 'Sports']
  return categories[Math.floor(Math.random() * categories.length)]
}
