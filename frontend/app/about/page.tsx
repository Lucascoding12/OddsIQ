"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function AboutPage() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)

  function handleSubscribe(e: React.FormEvent) {
    e.preventDefault()
    setSubmitted(true)
    setEmail("")
  }

  return (
    <div className="max-w-2xl mx-auto space-y-20 py-10">

      {/* Origin */}
      <div className="space-y-6">
        <div className="text-xs font-mono text-primary uppercase tracking-widest">Our Mission</div>
        <h1 className="text-4xl font-bold tracking-tight leading-tight">
          Sportsbooks have been winning for <span className="text-primary">too long.</span>
        </h1>
        <div className="space-y-4 text-muted-foreground leading-relaxed">
          <p>
            Most people who bet on sports are not losing because they pick the wrong teams.
            They are losing because they never understood the math. Sportsbooks build their
            edge directly into every line — the vig, the juice, the hold. It is baked in before
            the game even starts. Prediction markets do the same thing.
          </p>
          <p>
            For years, the tools to fight back — line shopping, expected value calculators,
            no-vig fair odds, Kelly sizing, CLV tracking — existed only inside the walls of
            professional betting syndicates and quant trading desks. The average bettor never
            had access to them. The house liked it that way.
          </p>
        </div>
      </div>

      {/* Story */}
      <div className="space-y-6">
        <div className="text-xs font-mono text-primary uppercase tracking-widest">How This Started</div>
        <div className="space-y-4 text-muted-foreground leading-relaxed">
          <p>
            OddsIQ started as a personal project. I was losing money betting and I wanted to understand
            why. As a data science student studying probability, statistics, and modeling, I knew the
            math existed to make better decisions — I just did not have a tool that put it all in one place.
          </p>
          <p>
            So I built one for myself. Once I understood expected value, closing line value, and how
            to properly size bets using the Kelly Criterion, the way I looked at betting completely changed.
            It stopped being gambling and started being a math problem.
          </p>
          <p>
            Then I looked around and realized how many people were in the same position I had been in —
            betting blind, losing steadily, with no idea that the sportsbook had a structural edge on
            every single wager they placed. Prediction markets are doing the same thing to a new generation
            of people who think they are being smart.
          </p>
          <p className="text-foreground font-medium">
            That is when the project stopped being just for me.
          </p>
        </div>
      </div>

      {/* Mission pillars */}
      <div className="space-y-6">
        <div className="text-xs font-mono text-primary uppercase tracking-widest">What We Stand For</div>
        <div className="space-y-4">
          <div className="border rounded-lg p-5 space-y-2">
            <h3 className="font-semibold">Free education, no paywalls</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Every calculator, every tool, every concept on OddsIQ is free. The math that sportsbooks
              use against you should not cost you anything to learn. If you understand implied probability,
              vig, and expected value, you are already a sharper bettor than most.
            </p>
          </div>
          <div className="border rounded-lg p-5 space-y-2">
            <h3 className="font-semibold">Level the playing field</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Sportsbooks employ quantitative analysts, traders, and sophisticated pricing models.
              You should have access to the same math. OddsIQ gives every bettor professional-grade
              tools — line shopping, arbitrage detection, CLV tracking, and Kelly staking — built
              on the same principles the sharps use.
            </p>
          </div>
          <div className="border rounded-lg p-5 space-y-2">
            <h3 className="font-semibold">Think like an investor, not a gambler</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Profitable betting is not about picking winners. It is about finding edges, sizing bets
              correctly, and making decisions with positive expected value over a large sample. OddsIQ
              is built to help you think about your bankroll like a portfolio — not a slot machine.
            </p>
          </div>
        </div>
      </div>

      {/* Builder */}
      <div className="space-y-6">
        <div className="text-xs font-mono text-primary uppercase tracking-widest">Builder</div>
        <div className="flex gap-5 items-start">
          <div className="w-11 h-11 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-primary font-bold text-base shrink-0">
            L
          </div>
          <div className="space-y-1.5">
            <div className="font-semibold">Lucas Simon</div>
            <div className="text-sm text-muted-foreground">Data Science · Finance · Statistics</div>
            <p className="text-sm text-muted-foreground leading-relaxed pt-1">
              I am a student applying what I study — probability, statistical modeling, and programming —
              to one of the most data-rich environments that exists: sports betting markets.
              OddsIQ is the platform I wish existed when I started. Building it in the open,
              keeping it free, and putting the math in everyone&apos;s hands.
            </p>
          </div>
        </div>
      </div>

      {/* Newsletter */}
      <div className="space-y-5 border rounded-lg p-6">
        <div className="space-y-1">
          <h3 className="font-semibold text-lg">Stay informed</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Major line movements. Arbitrage windows. New tools and betting market insights.
            No picks. No hype. Just the math — when it matters.
          </p>
        </div>
        {submitted ? (
          <div className="rounded-md border border-primary/30 bg-primary/5 px-4 py-3 text-sm">
            You are on the list.
          </div>
        ) : (
          <form onSubmit={handleSubscribe} className="flex gap-2 max-w-sm">
            <Input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="flex-1"
            />
            <Button type="submit">Subscribe</Button>
          </form>
        )}
      </div>

    </div>
  )
}
