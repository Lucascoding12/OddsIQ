import Link from "next/link"

const FEATURES = [
  {
    title: "Odds Board",
    href: "/odds",
    description: "Best available lines across 80+ sportsbooks updated every 30 seconds.",
  },
  {
    title: "Line Shopping",
    href: "/line-shopping",
    description: "Compare every book side by side for any game and bet type.",
  },
  {
    title: "15 Calculators",
    href: "/calculator",
    description: "EV, Kelly, No-Vig, Arbitrage, Parlay, CLV — the full toolkit.",
  },
  {
    title: "PnL Tracker",
    href: "/pnl",
    description: "Log every bet and track your ROI, win rate, and closing line value.",
  },
  {
    title: "Price Alerts",
    href: "/alerts",
    description: "Get notified the moment a line hits your target at any book.",
  },
  {
    title: "Sharp Metrics",
    href: "/sharp",
    description: "Steam moves, reverse line movement, and CLV — tools the pros use.",
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-[calc(100vh-56px)] flex flex-col">

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center text-center px-4 py-24 space-y-8">
        <div className="space-y-4 max-w-3xl">
          <div className="inline-block text-xs font-mono text-primary uppercase tracking-widest border border-primary/30 rounded-full px-3 py-1 bg-primary/5">
            Free. No paywalls. Ever.
          </div>
          <h1 className="text-5xl sm:text-6xl font-bold tracking-tight leading-tight">
            The math the sportsbooks<br />
            <span className="text-primary">don&apos;t want you to know.</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
            Professional-grade betting tools — odds shopping, EV calculators, arbitrage detection,
            and bankroll management — completely free. Level the playing field.
          </p>
        </div>

        <div className="flex gap-3">
          <Link
            href="/auth/register"
            className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity shadow-lg shadow-[#6366f1]/30"
          >
            Get started free
          </Link>
          <Link
            href="/auth/login"
            className="px-6 py-2.5 rounded-lg text-sm font-semibold border border-border text-muted-foreground hover:text-foreground hover:border-primary/50 transition-colors"
          >
            Log in
          </Link>
        </div>

        <p className="text-xs text-muted-foreground">
          No credit card. No subscription. Just the tools.
        </p>
      </div>

      {/* Feature grid */}
      <div className="border-t border-border/50 px-4 py-16">
        <div className="max-w-5xl mx-auto space-y-10">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Everything in one place</h2>
            <p className="text-sm text-muted-foreground">
              Create a free account to access all tools and keep your data organized.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f) => (
              <Link
                key={f.href}
                href="/auth/register"
                className="group rounded-lg border border-border bg-card p-5 space-y-2 hover:border-primary/40 hover:bg-primary/5 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-sm">{f.title}</h3>
                  <span className="text-muted-foreground group-hover:text-primary transition-colors text-xs">→</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{f.description}</p>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="border-t border-border/50 px-4 py-16 text-center space-y-5">
        <h2 className="text-2xl font-bold">Ready to stop guessing?</h2>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Join bettors who treat their bankroll like a portfolio. Free tools, real math, no noise.
        </p>
        <Link
          href="/auth/register"
          className="inline-block px-8 py-3 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:opacity-90 transition-opacity shadow-lg shadow-[#6366f1]/30"
        >
          Create free account
        </Link>
      </div>

    </div>
  )
}
