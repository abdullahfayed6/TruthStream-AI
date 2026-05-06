'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Shield, 
  Menu,
  X,
  Wifi,
  WifiOff
} from 'lucide-react'

interface HeaderProps {
  onMenuToggle?: () => void
  menuOpen?: boolean
  isConnected?: boolean
}

export function Header({ onMenuToggle, menuOpen, isConnected = false }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={onMenuToggle}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-foreground tracking-tight">
                TruthStream<span className="text-primary">AI</span>
              </h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest hidden sm:block">
                Real-Time Fake News Detection
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge 
            variant="outline" 
            className={`hidden sm:flex items-center gap-1.5 px-3 py-1 ${
              isConnected 
                ? 'border-primary/30' 
                : 'border-destructive/30'
            }`}
          >
            {isConnected ? (
              <>
                <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                <Wifi className="h-3 w-3 text-primary" />
                <span className="text-xs">System Online</span>
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-destructive" />
                <WifiOff className="h-3 w-3 text-destructive" />
                <span className="text-xs">Connecting...</span>
              </>
            )}
          </Badge>
        </div>
      </div>
    </header>
  )
}
