"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV_LINKS = [
  { href: "/", label: "Odds Board" },
  { href: "/line-shopping", label: "Line Shopping" },
  { href: "/alerts", label: "Alerts" },
  { href: "/pnl", label: "PnL" },
  { href: "/arbitrage", label: "Arbitrage" },
  { href: "/sharp", label: "Sharp Metrics" },
]

export function Navbar() {
  const pathname = usePathname()

  return (
    <nav className="border-b bg-background">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <Link href="/" className="font-bold text-lg tracking-tight">
          OddsIQ
        </Link>
        <div className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                pathname === link.href
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="ml-4 flex gap-2">
            <Link
              href="/auth/login"
              className="px-3 py-1.5 rounded-md text-sm border hover:bg-accent transition-colors"
            >
              Log in
            </Link>
            <Link
              href="/auth/register"
              className="px-3 py-1.5 rounded-md text-sm bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
