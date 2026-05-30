"use client"

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

  function handleLogout() {
    logout()
    router.push("/")
  }

  return (
    <nav className="border-b border-border/50 bg-background/95 backdrop-blur sticky top-0 z-10">
      <div className="w-full px-6 flex items-center h-14">
        <Link href="/" className="font-bold text-lg tracking-tight shrink-0 mr-6">
          Odds<span className="text-primary">IQ</span>
        </Link>

        <div className="flex flex-1 items-center">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`flex-1 text-center py-1.5 text-sm font-medium transition-colors rounded-lg relative ${
                pathname === link.href
                  ? "text-primary after:absolute after:bottom-0 after:left-1/2 after:-translate-x-1/2 after:w-4 after:h-px after:bg-primary after:rounded-full"
                  : "text-muted-foreground hover:text-foreground hover:bg-primary/10"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="flex gap-2 ml-6 shrink-0 items-center">
          {isLoggedIn ? (
            <>
              <span className="text-xs text-muted-foreground hidden sm:block truncate max-w-32">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 rounded-lg text-sm font-medium text-muted-foreground border border-border hover:text-foreground hover:border-primary/50 transition-colors"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/auth/login"
                className="px-3 py-1.5 rounded-lg text-sm font-medium text-muted-foreground border border-border hover:text-foreground hover:border-primary/50 transition-colors"
              >
                Log in
              </Link>
              <Link
                href="/auth/register"
                className="px-3 py-1.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 transition-opacity shadow-lg shadow-[#6366f1]/30"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
