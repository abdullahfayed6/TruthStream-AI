/**
 * TruthStream AI — API client for the FastAPI backend.
 * 
 * All API calls go through this module for centralized error handling,
 * base URL configuration, and type safety.
 */

import type {
  PaginatedArticles,
  SystemStats,
  TimelineEntry,
  GPTResponse,
  ArticleInput,
  Article,
} from './types'

// ─────────────────────────── Configuration ──────────────────────────

/**
 * API base URL — reads from NEXT_PUBLIC_API_URL environment variable.
 * Falls back to localhost:8000 for local development.
 * 
 * In browser, we use the external URL (localhost:8000).
 * In Docker, the env var points to http://api:8000 but the browser
 * always hits the host-mapped port.
 */
function getApiBaseUrl(): string {
  // In the browser, always use relative or localhost
  if (typeof window !== 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }
  // On the server side (SSR)
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}

function getWsBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const httpUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    return httpUrl
  }
  return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
}

export const API_BASE_URL = getApiBaseUrl()
export const WS_BASE_URL = getWsBaseUrl()

// ─────────────────────────── Fetch Helper ───────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const errorBody = await res.text().catch(() => 'Unknown error')
    throw new Error(`API Error ${res.status}: ${errorBody}`)
  }

  return res.json()
}

// ─────────────────────────── Articles ───────────────────────────────

export async function fetchArticles(params?: {
  label?: 'Fake' | 'Real' | 'all'
  source?: string
  page?: number
  page_size?: number
}): Promise<PaginatedArticles> {
  const searchParams = new URLSearchParams()
  if (params?.label && params.label !== 'all') searchParams.set('label', params.label)
  if (params?.source) searchParams.set('source', params.source)
  if (params?.page) searchParams.set('page', String(params.page))
  if (params?.page_size) searchParams.set('page_size', String(params.page_size))

  const query = searchParams.toString()
  return apiFetch<PaginatedArticles>(`/articles${query ? `?${query}` : ''}`)
}

export async function fetchArticle(articleId: string): Promise<Article> {
  return apiFetch<Article>(`/articles/${articleId}`)
}

// ─────────────────────────── Statistics ─────────────────────────────

export async function fetchStats(): Promise<SystemStats> {
  return apiFetch<SystemStats>('/stats')
}

export async function fetchTimeline(hours: number = 24): Promise<TimelineEntry[]> {
  return apiFetch<TimelineEntry[]>(`/stats/timeline?hours=${hours}`)
}

// ─────────────────────────── GPT Endpoints ─────────────────────────

export async function explainArticle(input: ArticleInput): Promise<GPTResponse> {
  return apiFetch<GPTResponse>('/explain', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export async function summarizeArticle(input: ArticleInput): Promise<GPTResponse> {
  return apiFetch<GPTResponse>('/summarize', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

// ─────────────────────────── Health Check ───────────────────────────

export async function checkHealth(): Promise<{ status: string; service: string }> {
  return apiFetch('/health')
}

// ─────────────────────────── SWR Fetchers ──────────────────────────

/** Generic fetcher for SWR — just wraps apiFetch */
export const swrFetcher = <T>(path: string): Promise<T> => apiFetch<T>(path)
