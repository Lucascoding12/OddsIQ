"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"

const NAV_LINKS = [
  { href: "/odds", label: "Odds Board" },
  { href: "/line-shopping", label: "Line Shopping" },
  { href: "/alerts", label: "Alerts" },
  { href: "/pnl", label: "PnL" },
  { href: "/arbitrage", label: "Arbitrage" },
  { href: "/sharp", label: "Sharp Metrics" },
  { href: "/calculator", label: "Calculator" },
  { href: "/about", label: "About" },
]

export function Navbar() {
  const pathname = usePathname()
  const { isLoggedIn, user, logout } = useAuth()
  const router = useRouter()
  const [menuOpen, setMenuOpen] = useState(false)

  function handleLogout() {
    logout()
    setMenuOpen(false)
    router.push("/")
  }

  const linkClass = (href: string) =>
    `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
      pathname === href
        ? "bg-primary/15 text-primary"
        : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
    }`

  return (
    <nav className="sticky top-0 z-20 border-b border-border/50 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4">
        <Link
          href="/"
          className="mr-1 shrink-0 text-lg font-bold tracking-tight"
          onClick={() => setMenuOpen(false)}
        >
          Odds<span className="text-primary">IQ</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden flex-1 items-center gap-0.5 lg:flex">
          {NAV_LINKS.map((link) => (
            <Link key={link.href} href={link.href} className={linkClass(link.href)}>
              {link.label}
            </Link>
          ))}
        </div>

        {/* Desktop auth */}
        <div className="ml-auto hidden shrink-0 items-center gap-2 lg:flex">
          {isLoggedIn ? (
            <>
              <span className="hidden max-w-36 truncate text-xs text-muted-foreground xl:block">
                {user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/auth/login"
                className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
              >
                Log in
              </Link>
              <Link
                href="/auth/register"
                className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground shadow-lg shadow-[#6366f1]/30 transition-opacity hover:opacity-90"
              >
                Sign up
              </Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMenuOpen((v) => !v)}
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          aria-expanded={menuOpen}
          className="ml-auto rounded-lg border border-border p-2 text-muted-foreground transition-colors hover:text-foreground lg:hidden"
        >
          {menuOpen ? (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 4h12M2 8h12M2 12h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="space-y-1 border-t border-border/50 bg-background/95 px-4 py-3 backdrop-blur-md lg:hidden">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={`block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                pathname === link.href
                  ? "bg-primary/15 text-primary"
                  : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="flex items-center gap-2 border-t border-border/50 pt-3">
            {isLoggedIn ? (
              <>
                <span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{user?.email}</span>
                <button
                  onClick={handleLogout}
                  className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  onClick={() => setMenuOpen(false)}
                  className="flex-1 rounded-lg border border-border px-3 py-2 text-center text-sm font-medium text-muted-foreground"
                >
                  Log in
                </Link>
                <Link
                  href="/auth/register"
                  onClick={() => setMenuOpen(false)}
                  className="flex-1 rounded-lg bg-primary px-3 py-2 text-center text-sm font-medium text-primary-foreground"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
