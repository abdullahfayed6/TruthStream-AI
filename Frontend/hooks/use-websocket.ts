/**
 * TruthStream AI — WebSocket hook for real-time article streaming.
 * 
 * Connects to the FastAPI WebSocket endpoint and pushes new articles
 * to the component via a callback. Includes auto-reconnect logic.
 */

'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { WS_BASE_URL } from '@/lib/api'
import type { Article, WSMessage } from '@/lib/types'

interface UseWebSocketOptions {
  /** Called when new articles arrive via WS */
  onNewArticles?: (articles: Article[]) => void
  /** Enable/disable the connection */
  enabled?: boolean
}

interface UseWebSocketReturn {
  /** Whether the WebSocket is currently connected */
  isConnected: boolean
  /** Total number of articles received via WS since mount */
  articleCount: number
  /** Last source that sent an article */
  lastSource: string | null
  /** Any connection error message */
  error: string | null
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { onNewArticles, enabled = true } = options
  const [isConnected, setIsConnected] = useState(false)
  const [articleCount, setArticleCount] = useState(0)
  const [lastSource, setLastSource] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const onNewArticlesRef = useRef(onNewArticles)

  // Keep callback ref fresh without triggering reconnect
  useEffect(() => {
    onNewArticlesRef.current = onNewArticles
  }, [onNewArticles])

  const connect = useCallback(() => {
    if (!enabled) return

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/articles`)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log('[WS] Connected to article stream')
      }

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data)

          switch (message.type) {
            case 'new_articles':
              setArticleCount(prev => prev + message.count)
              if (message.articles.length > 0) {
                setLastSource(message.articles[0].source)
              }
              onNewArticlesRef.current?.(message.articles)
              break

            case 'heartbeat':
              // Connection is alive, nothing to do
              break

            case 'error':
              console.warn('[WS] Server error:', message.message)
              setError(message.message)
              break
          }
        } catch (e) {
          console.error('[WS] Failed to parse message:', e)
        }
      }

      ws.onerror = () => {
        setError('WebSocket connection error')
        setIsConnected(false)
      }

      ws.onclose = () => {
        setIsConnected(false)
        console.log('[WS] Disconnected, will reconnect in 5s...')

        // Auto-reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, 5000)
      }
    } catch (e) {
      setError('Failed to connect to WebSocket')
      setIsConnected(false)

      // Retry after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, 5000)
    }
  }, [enabled])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  return { isConnected, articleCount, lastSource, error }
}
