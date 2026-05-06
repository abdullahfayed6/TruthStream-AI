/**
 * TruthStream AI — SWR hooks for real-time data fetching.
 * 
 * Uses SWR (stale-while-revalidate) for automatic caching, revalidation,
 * and polling to keep dashboard data fresh.
 */

'use client'

import useSWR from 'swr'
import {
  fetchStats,
  fetchTimeline,
  fetchArticles,
  API_BASE_URL,
} from '@/lib/api'
import type {
  SystemStats,
  TimelineEntry,
  PaginatedArticles,
} from '@/lib/types'

// ─────────────────────────── Stats Hook ─────────────────────────────

export function useStats(refreshInterval: number = 10000) {
  return useSWR<SystemStats>(
    'stats',
    () => fetchStats(),
    {
      refreshInterval,
      revalidateOnFocus: true,
      dedupingInterval: 5000,
    }
  )
}

// ─────────────────────────── Timeline Hook ──────────────────────────

export function useTimeline(hours: number = 24, refreshInterval: number = 30000) {
  return useSWR<TimelineEntry[]>(
    `timeline-${hours}`,
    () => fetchTimeline(hours),
    {
      refreshInterval,
      revalidateOnFocus: true,
      dedupingInterval: 15000,
    }
  )
}

// ─────────────────────────── Articles Hook ──────────────────────────

export function useArticles(
  params?: {
    label?: 'Fake' | 'Real' | 'all'
    source?: string
    page?: number
    page_size?: number
  },
  refreshInterval: number = 8000
) {
  const key = `articles-${params?.label || 'all'}-${params?.source || ''}-${params?.page || 1}-${params?.page_size || 20}`
  
  return useSWR<PaginatedArticles>(
    key,
    () => fetchArticles(params),
    {
      refreshInterval,
      revalidateOnFocus: true,
      dedupingInterval: 3000,
    }
  )
}

// ─────────────────────────── Health Hook ─────────────────────────────

export function useHealth(refreshInterval: number = 30000) {
  return useSWR<{ status: string; service: string }>(
    'health',
    async () => {
      const res = await fetch(`${API_BASE_URL}/health`)
      if (!res.ok) throw new Error('API unreachable')
      return res.json()
    },
    {
      refreshInterval,
      revalidateOnFocus: true,
      errorRetryCount: 3,
      errorRetryInterval: 5000,
    }
  )
}
