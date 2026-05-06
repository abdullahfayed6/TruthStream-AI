'use client'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  LayoutDashboard, 
  Newspaper, 
  Workflow
} from 'lucide-react'

interface SidebarNavProps {
  activeTab: string
  onTabChange: (tab: string) => void
  className?: string
  totalArticles?: number
}

function formatCount(n: number | undefined): string {
  if (!n) return '0'
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return n.toString()
}

const navItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    badge: null
  },
  {
    id: 'articles',
    label: 'Articles',
    icon: Newspaper,
    badge: 'dynamic' // Will be replaced with real count
  },
  {
    id: 'architecture',
    label: 'Architecture',
    icon: Workflow,
    badge: null
  }
]

export function SidebarNav({ activeTab, onTabChange, className, totalArticles }: SidebarNavProps) {
  return (
    <aside className={cn("flex flex-col h-full bg-sidebar border-r border-sidebar-border", className)}>
      <nav className="flex-1 p-4 space-y-1">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3 px-3">
          Navigation
        </p>
        {navItems.map((item) => (
          <Button
            key={item.id}
            variant={activeTab === item.id ? 'secondary' : 'ghost'}
            className={cn(
              "w-full justify-start gap-3 h-10",
              activeTab === item.id && "bg-sidebar-accent text-sidebar-accent-foreground"
            )}
            onClick={() => onTabChange(item.id)}
          >
            <item.icon className="h-4 w-4" />
            <span className="flex-1 text-left">{item.label}</span>
            {item.badge === 'dynamic' && (
              <Badge variant="outline" className="text-[10px] h-5 px-1.5 font-mono">
                {formatCount(totalArticles)}
              </Badge>
            )}
          </Button>
        ))}
      </nav>
    </aside>
  )
}
