# OddsIQ Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full OddsIQ app with all pages, navigation, and placeholder API routes — no real data yet, just working routes and buttons.

**Architecture:** Next.js 14 App Router frontend with a FastAPI backend, wired together via a Docker Compose local environment. All pages render with mock/hardcoded data and functional navigation; real data fetching comes in the next phase.

**Tech Stack:** Next.js 14, Tailwind CSS, shadcn/ui, FastAPI, Docker Compose, pnpm, uv

---

## File Map

### Frontend (`frontend/`)
| File | Responsibility |
|------|---------------|
| `app/layout.tsx` | Root layout — wraps all pages with `<Navbar>` |
| `app/page.tsx` | Odds Board (home) — table of games + best lines |
| `app/line-shopping/page.tsx` | Line Shopping — pick a game, see all books side-by-side |
| `app/alerts/page.tsx` | Alerts — list of user alerts, create alert form |
| `app/pnl/page.tsx` | PnL Dashboard — bet log table + summary stats |
| `app/arbitrage/page.tsx` | Arb Calculator — manual input + results panel |
| `app/sharp/page.tsx` | Sharp Metrics — CLV, line movement, steam moves |
| `app/auth/login/page.tsx` | Login form |
| `app/auth/register/page.tsx` | Register form |
| `components/nav/Navbar.tsx` | Top nav with links to all pages |
| `components/odds/OddsTable.tsx` | Reusable table of games + best odds |
| `components/odds/BookComparison.tsx` | Side-by-side book odds for one game |
| `components/bets/BetLogTable.tsx` | Table of logged bets |
| `components/bets/BetForm.tsx` | Form to log a new bet |
| `components/alerts/AlertList.tsx` | List of active alerts |
| `components/alerts/AlertForm.tsx` | Form to create a new alert |
| `components/arb/ArbCalculator.tsx` | Two-leg arb input + profit output |
| `components/sharp/ClvPanel.tsx` | CLV stat display |
| `components/sharp/LineMovementPanel.tsx` | Line movement display |
| `lib/mock-data.ts` | All mock data used across pages |

### Backend (`backend/`)
| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app entry point, mounts routers |
| `api/v1/odds.py` | GET /api/v1/odds — returns mock odds list |
| `api/v1/alerts.py` | GET/POST /api/v1/alerts — mock alert CRUD |
| `api/v1/bets.py` | GET/POST /api/v1/bets — mock bet log CRUD |
| `api/v1/arb.py` | POST /api/v1/arb/calculate — arb calc logic |
| `api/v1/sharp.py` | GET /api/v1/sharp — mock CLV + steam data |

### Root
| File | Responsibility |
|------|---------------|
| `docker-compose.yml` | Runs frontend + backend together |
| `frontend/package.json` | JS dependencies |
| `backend/pyproject.toml` | Python dependencies |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `frontend/` (Next.js app)
- Create: `backend/` (FastAPI app)
- Create: `docker-compose.yml`

- [ ] **Step 1: Bootstrap Next.js frontend**

```bash
cd /Users/lucassimon/OddsIQ
pnpm create next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
```

Expected: `frontend/` directory created with App Router structure.

- [ ] **Step 2: Install frontend dependencies**

```bash
cd frontend
pnpm add swr
pnpm add -D @types/node
```

- [ ] **Step 3: Install shadcn/ui**

```bash
cd /Users/lucassimon/OddsIQ/frontend
pnpm dlx shadcn@latest init -d
```

When prompted: style = Default, base color = Slate, CSS variables = yes.

Then add the components we'll use:
```bash
pnpm dlx shadcn@latest add button input label card table badge tabs dialog
```

- [ ] **Step 4: Bootstrap FastAPI backend**

```bash
cd /Users/lucassimon/OddsIQ
mkdir backend && cd backend
uv init --no-readme
uv add fastapi "uvicorn[standard]" pydantic
```

- [ ] **Step 5: Create backend entry point**

Create `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1 import odds, alerts, bets, arb, sharp

app = FastAPI(title="OddsIQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(odds.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(bets.router, prefix="/api/v1")
app.include_router(arb.router, prefix="/api/v1")
app.include_router(sharp.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}
```

Create `backend/api/__init__.py` and `backend/api/v1/__init__.py` (both empty).

- [ ] **Step 6: Create docker-compose.yml**

Create `/Users/lucassimon/OddsIQ/docker-compose.yml`:
```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    command: uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv sync
COPY . .
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 7: Verify backend starts**

```bash
cd /Users/lucassimon/OddsIQ/backend
uv run uvicorn main:app --reload
```

Open http://localhost:8000/health — should return `{"status": "ok"}`.
Stop with Ctrl+C.

- [ ] **Step 8: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git init
git add .
git commit -m "feat: scaffold Next.js frontend and FastAPI backend"
```

---

## Task 2: Mock Data

**Files:**
- Create: `frontend/lib/mock-data.ts`

- [ ] **Step 1: Create mock data file**

Create `frontend/lib/mock-data.ts`:
```typescript
export type Game = {
  id: string
  sport: "NFL" | "NBA" | "MLB" | "NHL"
  homeTeam: string
  awayTeam: string
  commenceTime: string
  bestLine: {
    homeMoneyline: number
    awayMoneyline: number
    spread: number
    spreadOdds: number
    total: number
    overOdds: number
    underOdds: number
    book: string
  }
}

export type BookOdds = {
  book: string
  homeMoneyline: number
  awayMoneyline: number
  spread: number
  spreadOdds: number
  total: number
  overOdds: number
  underOdds: number
}

export type Alert = {
  id: string
  game: string
  betType: string
  targetOdds: number
  book: string | "any"
  status: "active" | "triggered"
  createdAt: string
}

export type Bet = {
  id: string
  date: string
  sport: string
  game: string
  betType: string
  odds: number
  stake: number
  result: "win" | "loss" | "pending"
  pnl: number
  closingOdds: number
  clv: number
}

export const MOCK_GAMES: Game[] = [
  {
    id: "1",
    sport: "NFL",
    homeTeam: "Kansas City Chiefs",
    awayTeam: "Buffalo Bills",
    commenceTime: "2026-09-10T20:20:00Z",
    bestLine: { homeMoneyline: -150, awayMoneyline: 130, spread: -3, spreadOdds: -110, total: 47.5, overOdds: -110, underOdds: -110, book: "DraftKings" },
  },
  {
    id: "2",
    sport: "NBA",
    homeTeam: "Boston Celtics",
    awayTeam: "LA Lakers",
    commenceTime: "2026-11-01T19:00:00Z",
    bestLine: { homeMoneyline: -200, awayMoneyline: 170, spread: -5.5, spreadOdds: -108, total: 224.5, overOdds: -112, underOdds: -108, book: "FanDuel" },
  },
  {
    id: "3",
    sport: "MLB",
    homeTeam: "New York Yankees",
    awayTeam: "Boston Red Sox",
    commenceTime: "2026-07-04T19:05:00Z",
    bestLine: { homeMoneyline: -130, awayMoneyline: 110, spread: -1.5, spreadOdds: -140, total: 9, overOdds: -115, underOdds: -105, book: "BetMGM" },
  },
  {
    id: "4",
    sport: "NHL",
    homeTeam: "Toronto Maple Leafs",
    awayTeam: "Montreal Canadiens",
    commenceTime: "2026-10-15T19:30:00Z",
    bestLine: { homeMoneyline: -160, awayMoneyline: 140, spread: -1.5, spreadOdds: 120, total: 6, overOdds: -118, underOdds: -102, book: "Caesars" },
  },
]

export const MOCK_BOOK_ODDS: BookOdds[] = [
  { book: "DraftKings", homeMoneyline: -150, awayMoneyline: 130, spread: -3, spreadOdds: -110, total: 47.5, overOdds: -110, underOdds: -110 },
  { book: "FanDuel", homeMoneyline: -155, awayMoneyline: 133, spread: -3, spreadOdds: -112, total: 47.5, overOdds: -108, underOdds: -112 },
  { book: "BetMGM", homeMoneyline: -148, awayMoneyline: 128, spread: -3, spreadOdds: -110, total: 48, overOdds: -110, underOdds: -110 },
  { book: "Caesars", homeMoneyline: -152, awayMoneyline: 132, spread: -3.5, spreadOdds: -105, total: 47.5, overOdds: -112, underOdds: -108 },
  { book: "Pinnacle", homeMoneyline: -145, awayMoneyline: 138, spread: -3, spreadOdds: -107, total: 47.5, overOdds: -105, underOdds: -108 },
]

export const MOCK_ALERTS: Alert[] = [
  { id: "1", game: "Chiefs vs Bills", betType: "Away ML", targetOdds: 140, book: "any", status: "active", createdAt: "2026-05-28" },
  { id: "2", game: "Celtics vs Lakers", betType: "Home Spread -5.5", targetOdds: -108, book: "DraftKings", status: "triggered", createdAt: "2026-05-27" },
]

export const MOCK_BETS: Bet[] = [
  { id: "1", date: "2026-05-20", sport: "NFL", game: "Chiefs vs Bills", betType: "Chiefs ML", odds: -150, stake: 100, result: "win", pnl: 66.67, closingOdds: -165, clv: 15 },
  { id: "2", date: "2026-05-18", sport: "NBA", game: "Celtics vs Lakers", betType: "Celtics -5.5", odds: -108, stake: 50, result: "loss", pnl: -50, closingOdds: -112, clv: 4 },
  { id: "3", date: "2026-05-15", sport: "MLB", game: "Yankees vs Red Sox", betType: "Over 9", odds: -115, stake: 75, result: "win", pnl: 65.22, closingOdds: -118, clv: 3 },
  { id: "4", date: "2026-05-29", sport: "NHL", game: "Leafs vs Habs", betType: "Leafs ML", odds: -160, stake: 100, result: "pending", pnl: 0, closingOdds: -160, clv: 0 },
]
```

- [ ] **Step 2: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/lib/mock-data.ts
git commit -m "feat: add mock data types and fixtures"
```

---

## Task 3: Navbar Component

**Files:**
- Create: `frontend/components/nav/Navbar.tsx`
- Modify: `frontend/app/layout.tsx`

- [ ] **Step 1: Create Navbar**

Create `frontend/components/nav/Navbar.tsx`:
```tsx
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
```

- [ ] **Step 2: Wire Navbar into root layout**

Replace the contents of `frontend/app/layout.tsx`:
```tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Navbar } from "@/components/nav/Navbar"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "OddsIQ",
  description: "Sports odds aggregation and sharp analytics",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Start dev server and verify nav renders**

```bash
cd /Users/lucassimon/OddsIQ/frontend
pnpm dev
```

Open http://localhost:3000 — should see the navbar with all links. Click each link to verify Next.js routing works (pages will 404 until created).

- [ ] **Step 4: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/nav/Navbar.tsx frontend/app/layout.tsx
git commit -m "feat: add Navbar with all route links"
```

---

## Task 4: Odds Board (Home Page)

**Files:**
- Create: `frontend/components/odds/OddsTable.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Create OddsTable component**

Create `frontend/components/odds/OddsTable.tsx`:
```tsx
import { Game } from "@/lib/mock-data"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const SPORT_COLORS: Record<string, string> = {
  NFL: "bg-amber-100 text-amber-800",
  NBA: "bg-blue-100 text-blue-800",
  MLB: "bg-red-100 text-red-800",
  NHL: "bg-slate-100 text-slate-800",
}

function formatOdds(odds: number) {
  return odds > 0 ? `+${odds}` : `${odds}`
}

type Props = { games: Game[] }

export function OddsTable({ games }: Props) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Game</th>
            <th className="text-left px-4 py-3 font-medium">Sport</th>
            <th className="text-right px-4 py-3 font-medium">Moneyline</th>
            <th className="text-right px-4 py-3 font-medium">Spread</th>
            <th className="text-right px-4 py-3 font-medium">Total</th>
            <th className="text-right px-4 py-3 font-medium">Best Book</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y">
          {games.map((game) => (
            <tr key={game.id} className="hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 font-medium">
                {game.awayTeam} @ {game.homeTeam}
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${SPORT_COLORS[game.sport]}`}>
                  {game.sport}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <span className="text-green-600 font-medium">{formatOdds(game.bestLine.homeMoneyline)}</span>
                {" / "}
                <span>{formatOdds(game.bestLine.awayMoneyline)}</span>
              </td>
              <td className="px-4 py-3 text-right">
                {game.bestLine.spread > 0 ? "+" : ""}{game.bestLine.spread}{" "}
                ({formatOdds(game.bestLine.spreadOdds)})
              </td>
              <td className="px-4 py-3 text-right">
                {game.bestLine.total} (O/U {formatOdds(game.bestLine.overOdds)})
              </td>
              <td className="px-4 py-3 text-right text-muted-foreground text-xs">
                {game.bestLine.book}
              </td>
              <td className="px-4 py-3 text-right">
                <Button variant="outline" size="sm" asChild>
                  <a href={`/line-shopping?game=${game.id}`}>Compare</a>
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Build the home page**

Replace `frontend/app/page.tsx`:
```tsx
"use client"

import { useState } from "react"
import { OddsTable } from "@/components/odds/OddsTable"
import { MOCK_GAMES } from "@/lib/mock-data"
import { Button } from "@/components/ui/button"

const SPORTS = ["All", "NFL", "NBA", "MLB", "NHL"] as const

export default function OddsBoardPage() {
  const [activeSport, setActiveSport] = useState<string>("All")

  const filtered = activeSport === "All"
    ? MOCK_GAMES
    : MOCK_GAMES.filter((g) => g.sport === activeSport)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Odds Board</h1>
          <p className="text-sm text-muted-foreground mt-1">Best available lines across all books</p>
        </div>
        <span className="text-xs text-muted-foreground">Refreshes every 30s</span>
      </div>

      <div className="flex gap-2">
        {SPORTS.map((sport) => (
          <Button
            key={sport}
            variant={activeSport === sport ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveSport(sport)}
          >
            {sport}
          </Button>
        ))}
      </div>

      <OddsTable games={filtered} />
    </div>
  )
}
```

- [ ] **Step 3: Verify in browser**

Open http://localhost:3000 — should see the odds table with sport filter buttons. Click each sport filter and confirm filtering works.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/odds/OddsTable.tsx frontend/app/page.tsx
git commit -m "feat: add Odds Board page with sport filter"
```

---

## Task 5: Line Shopping Page

**Files:**
- Create: `frontend/components/odds/BookComparison.tsx`
- Create: `frontend/app/line-shopping/page.tsx`

- [ ] **Step 1: Create BookComparison component**

Create `frontend/components/odds/BookComparison.tsx`:
```tsx
import { BookOdds } from "@/lib/mock-data"
import { Badge } from "@/components/ui/badge"

function formatOdds(odds: number) {
  return odds > 0 ? `+${odds}` : `${odds}`
}

type Props = { books: BookOdds[] }

export function BookComparison({ books }: Props) {
  const bestML = Math.max(...books.map((b) => b.homeMoneyline))
  const bestSpreadOdds = Math.max(...books.map((b) => b.spreadOdds))
  const bestOverOdds = Math.max(...books.map((b) => b.overOdds))

  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Book</th>
            <th className="text-right px-4 py-3 font-medium">Home ML</th>
            <th className="text-right px-4 py-3 font-medium">Away ML</th>
            <th className="text-right px-4 py-3 font-medium">Spread</th>
            <th className="text-right px-4 py-3 font-medium">Spread Odds</th>
            <th className="text-right px-4 py-3 font-medium">Total</th>
            <th className="text-right px-4 py-3 font-medium">Over</th>
            <th className="text-right px-4 py-3 font-medium">Under</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {books.map((b) => (
            <tr key={b.book} className="hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 font-medium">{b.book}</td>
              <td className={`px-4 py-3 text-right font-medium ${b.homeMoneyline === bestML ? "text-green-600" : ""}`}>
                {formatOdds(b.homeMoneyline)}
              </td>
              <td className="px-4 py-3 text-right">{formatOdds(b.awayMoneyline)}</td>
              <td className="px-4 py-3 text-right">{b.spread > 0 ? "+" : ""}{b.spread}</td>
              <td className={`px-4 py-3 text-right ${b.spreadOdds === bestSpreadOdds ? "text-green-600 font-medium" : ""}`}>
                {formatOdds(b.spreadOdds)}
              </td>
              <td className="px-4 py-3 text-right">{b.total}</td>
              <td className={`px-4 py-3 text-right ${b.overOdds === bestOverOdds ? "text-green-600 font-medium" : ""}`}>
                {formatOdds(b.overOdds)}
              </td>
              <td className="px-4 py-3 text-right">{formatOdds(b.underOdds)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-4 py-2 bg-muted/30 text-xs text-muted-foreground">
        Green = best available line for that market
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create Line Shopping page**

Create `frontend/app/line-shopping/page.tsx`:
```tsx
"use client"

import { useState } from "react"
import { BookComparison } from "@/components/odds/BookComparison"
import { MOCK_GAMES, MOCK_BOOK_ODDS } from "@/lib/mock-data"

export default function LineShoppingPage() {
  const [selectedGameId, setSelectedGameId] = useState(MOCK_GAMES[0].id)
  const selectedGame = MOCK_GAMES.find((g) => g.id === selectedGameId)!

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Line Shopping</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Compare odds across all books for a single game
        </p>
      </div>

      <div className="flex items-center gap-3">
        <label className="text-sm font-medium">Select game:</label>
        <select
          className="border rounded-md px-3 py-1.5 text-sm bg-background"
          value={selectedGameId}
          onChange={(e) => setSelectedGameId(e.target.value)}
        >
          {MOCK_GAMES.map((g) => (
            <option key={g.id} value={g.id}>
              [{g.sport}] {g.awayTeam} @ {g.homeTeam}
            </option>
          ))}
        </select>
      </div>

      <div className="text-sm font-medium text-muted-foreground">
        Showing odds for: <span className="text-foreground">{selectedGame.awayTeam} @ {selectedGame.homeTeam}</span>
      </div>

      <BookComparison books={MOCK_BOOK_ODDS} />
    </div>
  )
}
```

- [ ] **Step 3: Verify in browser**

Open http://localhost:3000/line-shopping — should see a game selector dropdown and the book comparison table with green highlights on best lines.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/odds/BookComparison.tsx frontend/app/line-shopping/
git commit -m "feat: add Line Shopping page with book comparison table"
```

---

## Task 6: Alerts Page

**Files:**
- Create: `frontend/components/alerts/AlertList.tsx`
- Create: `frontend/components/alerts/AlertForm.tsx`
- Create: `frontend/app/alerts/page.tsx`

- [ ] **Step 1: Create AlertList component**

Create `frontend/components/alerts/AlertList.tsx`:
```tsx
import { Alert } from "@/lib/mock-data"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

type Props = { alerts: Alert[]; onDelete: (id: string) => void }

export function AlertList({ alerts, onDelete }: Props) {
  if (alerts.length === 0) {
    return <p className="text-sm text-muted-foreground py-8 text-center">No alerts set. Create one below.</p>
  }

  return (
    <div className="rounded-lg border divide-y">
      {alerts.map((alert) => (
        <div key={alert.id} className="flex items-center justify-between px-4 py-3">
          <div className="space-y-0.5">
            <div className="text-sm font-medium">{alert.game}</div>
            <div className="text-xs text-muted-foreground">
              {alert.betType} · Target: {alert.targetOdds > 0 ? "+" : ""}{alert.targetOdds} ·{" "}
              Book: {alert.book} · Created {alert.createdAt}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant={alert.status === "active" ? "default" : "secondary"}>
              {alert.status}
            </Badge>
            <Button variant="ghost" size="sm" onClick={() => onDelete(alert.id)}>
              Delete
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Create AlertForm component**

Create `frontend/components/alerts/AlertForm.tsx`:
```tsx
"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { MOCK_GAMES } from "@/lib/mock-data"

type Props = { onSubmit: (alert: { game: string; betType: string; targetOdds: number; book: string }) => void }

export function AlertForm({ onSubmit }: Props) {
  const [game, setGame] = useState(MOCK_GAMES[0].id)
  const [betType, setBetType] = useState("Home ML")
  const [targetOdds, setTargetOdds] = useState("")
  const [book, setBook] = useState("any")

  const BOOKS = ["any", "DraftKings", "FanDuel", "BetMGM", "Caesars", "Pinnacle"]
  const BET_TYPES = ["Home ML", "Away ML", "Home Spread", "Away Spread", "Over", "Under"]

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const selected = MOCK_GAMES.find((g) => g.id === game)!
    onSubmit({
      game: `${selected.awayTeam} @ ${selected.homeTeam}`,
      betType,
      targetOdds: Number(targetOdds),
      book,
    })
    setTargetOdds("")
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-4 space-y-4">
      <h2 className="font-semibold">Create Alert</h2>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label>Game</Label>
          <select
            className="w-full border rounded-md px-3 py-1.5 text-sm bg-background"
            value={game}
            onChange={(e) => setGame(e.target.value)}
          >
            {MOCK_GAMES.map((g) => (
              <option key={g.id} value={g.id}>
                {g.awayTeam} @ {g.homeTeam}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Bet Type</Label>
          <select
            className="w-full border rounded-md px-3 py-1.5 text-sm bg-background"
            value={betType}
            onChange={(e) => setBetType(e.target.value)}
          >
            {BET_TYPES.map((t) => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Target Odds (e.g. -110 or +150)</Label>
          <Input
            type="number"
            placeholder="-110"
            value={targetOdds}
            onChange={(e) => setTargetOdds(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label>Book</Label>
          <select
            className="w-full border rounded-md px-3 py-1.5 text-sm bg-background"
            value={book}
            onChange={(e) => setBook(e.target.value)}
          >
            {BOOKS.map((b) => <option key={b}>{b}</option>)}
          </select>
        </div>
      </div>
      <Button type="submit">Create Alert</Button>
    </form>
  )
}
```

- [ ] **Step 3: Create Alerts page**

Create `frontend/app/alerts/page.tsx`:
```tsx
"use client"

import { useState } from "react"
import { AlertList } from "@/components/alerts/AlertList"
import { AlertForm } from "@/components/alerts/AlertForm"
import { MOCK_ALERTS, Alert } from "@/lib/mock-data"

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(MOCK_ALERTS)

  function handleCreate(data: { game: string; betType: string; targetOdds: number; book: string }) {
    const newAlert: Alert = {
      id: String(Date.now()),
      status: "active",
      createdAt: new Date().toISOString().split("T")[0],
      ...data,
    }
    setAlerts((prev) => [newAlert, ...prev])
  }

  function handleDelete(id: string) {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Alerts</h1>
        <p className="text-sm text-muted-foreground mt-1">Get notified when a line hits your target</p>
      </div>
      <AlertList alerts={alerts} onDelete={handleDelete} />
      <AlertForm onSubmit={handleCreate} />
    </div>
  )
}
```

- [ ] **Step 4: Verify in browser**

Open http://localhost:3000/alerts — should see the alert list, be able to delete alerts, and create new ones via the form.

- [ ] **Step 5: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/alerts/ frontend/app/alerts/
git commit -m "feat: add Alerts page with create and delete"
```

---

## Task 7: PnL Dashboard Page

**Files:**
- Create: `frontend/components/bets/BetLogTable.tsx`
- Create: `frontend/components/bets/BetForm.tsx`
- Create: `frontend/app/pnl/page.tsx`

- [ ] **Step 1: Create BetLogTable**

Create `frontend/components/bets/BetLogTable.tsx`:
```tsx
import { Bet } from "@/lib/mock-data"
import { Badge } from "@/components/ui/badge"

function formatOdds(odds: number) {
  return odds > 0 ? `+${odds}` : `${odds}`
}

type Props = { bets: Bet[] }

export function BetLogTable({ bets }: Props) {
  return (
    <div className="rounded-lg border overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Date</th>
            <th className="text-left px-4 py-3 font-medium">Game</th>
            <th className="text-left px-4 py-3 font-medium">Bet</th>
            <th className="text-right px-4 py-3 font-medium">Odds</th>
            <th className="text-right px-4 py-3 font-medium">Stake</th>
            <th className="text-right px-4 py-3 font-medium">Result</th>
            <th className="text-right px-4 py-3 font-medium">PnL</th>
            <th className="text-right px-4 py-3 font-medium">Closing</th>
            <th className="text-right px-4 py-3 font-medium">CLV</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {bets.map((bet) => (
            <tr key={bet.id} className="hover:bg-muted/30 transition-colors">
              <td className="px-4 py-3 text-muted-foreground">{bet.date}</td>
              <td className="px-4 py-3">{bet.game}</td>
              <td className="px-4 py-3">{bet.betType}</td>
              <td className="px-4 py-3 text-right">{formatOdds(bet.odds)}</td>
              <td className="px-4 py-3 text-right">${bet.stake}</td>
              <td className="px-4 py-3 text-right">
                <Badge variant={bet.result === "win" ? "default" : bet.result === "loss" ? "destructive" : "secondary"}>
                  {bet.result}
                </Badge>
              </td>
              <td className={`px-4 py-3 text-right font-medium ${bet.pnl > 0 ? "text-green-600" : bet.pnl < 0 ? "text-red-500" : "text-muted-foreground"}`}>
                {bet.pnl > 0 ? "+" : ""}{bet.pnl === 0 ? "-" : `$${bet.pnl.toFixed(2)}`}
              </td>
              <td className="px-4 py-3 text-right text-muted-foreground">{formatOdds(bet.closingOdds)}</td>
              <td className={`px-4 py-3 text-right font-medium ${bet.clv > 0 ? "text-green-600" : bet.clv < 0 ? "text-red-500" : "text-muted-foreground"}`}>
                {bet.clv > 0 ? "+" : ""}{bet.clv === 0 ? "-" : `${bet.clv}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 2: Create BetForm**

Create `frontend/components/bets/BetForm.tsx`:
```tsx
"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Bet } from "@/lib/mock-data"

type Props = { onSubmit: (bet: Omit<Bet, "id" | "pnl" | "closingOdds" | "clv">) => void }

export function BetForm({ onSubmit }: Props) {
  const [form, setForm] = useState({ date: "", sport: "NFL", game: "", betType: "", odds: "", stake: "" })
  const SPORTS = ["NFL", "NBA", "MLB", "NHL"]

  function set(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({ ...form, odds: Number(form.odds), stake: Number(form.stake), result: "pending" })
    setForm({ date: "", sport: "NFL", game: "", betType: "", odds: "", stake: "" })
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border p-4 space-y-4">
      <h2 className="font-semibold">Log a Bet</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="space-y-1.5">
          <Label>Date</Label>
          <Input type="date" value={form.date} onChange={(e) => set("date", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Sport</Label>
          <select className="w-full border rounded-md px-3 py-1.5 text-sm bg-background" value={form.sport} onChange={(e) => set("sport", e.target.value)}>
            {SPORTS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label>Game</Label>
          <Input placeholder="Chiefs vs Bills" value={form.game} onChange={(e) => set("game", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Bet Type</Label>
          <Input placeholder="Chiefs ML" value={form.betType} onChange={(e) => set("betType", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Odds</Label>
          <Input type="number" placeholder="-110" value={form.odds} onChange={(e) => set("odds", e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>Stake ($)</Label>
          <Input type="number" placeholder="100" value={form.stake} onChange={(e) => set("stake", e.target.value)} required />
        </div>
      </div>
      <Button type="submit">Log Bet</Button>
    </form>
  )
}
```

- [ ] **Step 3: Create PnL page**

Create `frontend/app/pnl/page.tsx`:
```tsx
"use client"

import { useState } from "react"
import { BetLogTable } from "@/components/bets/BetLogTable"
import { BetForm } from "@/components/bets/BetForm"
import { MOCK_BETS, Bet } from "@/lib/mock-data"

export default function PnLPage() {
  const [bets, setBets] = useState<Bet[]>(MOCK_BETS)

  const settled = bets.filter((b) => b.result !== "pending")
  const totalPnl = settled.reduce((sum, b) => sum + b.pnl, 0)
  const wins = settled.filter((b) => b.result === "win").length
  const winRate = settled.length > 0 ? ((wins / settled.length) * 100).toFixed(1) : "0"
  const avgClv = settled.length > 0 ? (settled.reduce((sum, b) => sum + b.clv, 0) / settled.length).toFixed(1) : "0"

  function handleAdd(data: Omit<Bet, "id" | "pnl" | "closingOdds" | "clv">) {
    setBets((prev) => [{ id: String(Date.now()), pnl: 0, closingOdds: data.odds, clv: 0, ...data }, ...prev])
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">PnL Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Track your bets and performance</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total PnL", value: `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? "text-green-600" : "text-red-500" },
          { label: "Win Rate", value: `${winRate}%`, color: "" },
          { label: "Avg CLV", value: `${Number(avgClv) >= 0 ? "+" : ""}${avgClv}`, color: Number(avgClv) >= 0 ? "text-green-600" : "text-red-500" },
          { label: "Total Bets", value: String(bets.length), color: "" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg border px-4 py-3">
            <div className="text-xs text-muted-foreground">{stat.label}</div>
            <div className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      <BetLogTable bets={bets} />
      <BetForm onSubmit={handleAdd} />
    </div>
  )
}
```

- [ ] **Step 4: Verify in browser**

Open http://localhost:3000/pnl — should see 4 stat cards, the bet log table, and a form to add bets.

- [ ] **Step 5: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/bets/ frontend/app/pnl/
git commit -m "feat: add PnL dashboard with bet log and stat cards"
```

---

## Task 8: Arbitrage Calculator Page

**Files:**
- Create: `frontend/components/arb/ArbCalculator.tsx`
- Create: `frontend/app/arbitrage/page.tsx`

- [ ] **Step 1: Create ArbCalculator component**

Create `frontend/components/arb/ArbCalculator.tsx`:
```tsx
"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

function americanToDecimal(odds: number): number {
  if (odds > 0) return odds / 100 + 1
  return 100 / Math.abs(odds) + 1
}

function calcArb(leg1Odds: number, leg2Odds: number, totalStake: number) {
  const d1 = americanToDecimal(leg1Odds)
  const d2 = americanToDecimal(leg2Odds)
  const impliedProb = 1 / d1 + 1 / d2
  const isArb = impliedProb < 1
  const stake1 = (totalStake / d1) / impliedProb
  const stake2 = (totalStake / d2) / impliedProb
  const profit = isArb ? totalStake * (1 / impliedProb - 1) : 0
  return { impliedProb, isArb, stake1, stake2, profit }
}

export function ArbCalculator() {
  const [leg1, setLeg1] = useState({ book: "", odds: "" })
  const [leg2, setLeg2] = useState({ book: "", odds: "" })
  const [totalStake, setTotalStake] = useState("1000")
  const [result, setResult] = useState<ReturnType<typeof calcArb> | null>(null)

  function handleCalc(e: React.FormEvent) {
    e.preventDefault()
    setResult(calcArb(Number(leg1.odds), Number(leg2.odds), Number(totalStake)))
  }

  return (
    <form onSubmit={handleCalc} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: "Leg 1", state: leg1, set: setLeg1 },
          { label: "Leg 2", state: leg2, set: setLeg2 },
        ].map(({ label, state, set }) => (
          <div key={label} className="rounded-lg border p-4 space-y-3">
            <div className="font-medium text-sm">{label}</div>
            <div className="space-y-1.5">
              <Label>Book</Label>
              <Input placeholder="e.g. DraftKings" value={state.book} onChange={(e) => set((s) => ({ ...s, book: e.target.value }))} required />
            </div>
            <div className="space-y-1.5">
              <Label>American Odds</Label>
              <Input type="number" placeholder="-110" value={state.odds} onChange={(e) => set((s) => ({ ...s, odds: e.target.value }))} required />
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-end gap-4">
        <div className="space-y-1.5">
          <Label>Total Stake ($)</Label>
          <Input type="number" value={totalStake} onChange={(e) => setTotalStake(e.target.value)} className="w-36" required />
        </div>
        <Button type="submit">Calculate</Button>
      </div>

      {result && (
        <div className={`rounded-lg border p-4 space-y-3 ${result.isArb ? "border-green-500 bg-green-50" : "border-red-400 bg-red-50"}`}>
          <div className={`font-semibold ${result.isArb ? "text-green-700" : "text-red-600"}`}>
            {result.isArb ? "Arbitrage Opportunity Found!" : "No Arbitrage — Books are not in your favor"}
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">Implied probability total:</span> <span className="font-medium">{(result.impliedProb * 100).toFixed(2)}%</span></div>
            <div><span className="text-muted-foreground">Guaranteed profit:</span> <span className={`font-medium ${result.isArb ? "text-green-700" : ""}`}>${result.profit.toFixed(2)}</span></div>
            <div><span className="text-muted-foreground">Stake on Leg 1 ({leg1.book || "Book 1"}):</span> <span className="font-medium">${result.stake1.toFixed(2)}</span></div>
            <div><span className="text-muted-foreground">Stake on Leg 2 ({leg2.book || "Book 2"}):</span> <span className="font-medium">${result.stake2.toFixed(2)}</span></div>
          </div>
        </div>
      )}
    </form>
  )
}
```

- [ ] **Step 2: Create Arbitrage page**

Create `frontend/app/arbitrage/page.tsx`:
```tsx
import { ArbCalculator } from "@/components/arb/ArbCalculator"

export default function ArbitragePage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Arbitrage Calculator</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Enter odds from two books to find guaranteed-profit opportunities
        </p>
      </div>

      <div className="rounded-lg border p-4 bg-muted/30 text-sm space-y-1">
        <div className="font-medium">How arb betting works</div>
        <p className="text-muted-foreground">
          Arbitrage exists when the combined implied probability across books is below 100%.
          You bet both sides proportionally so you win regardless of outcome.
        </p>
      </div>

      <ArbCalculator />
    </div>
  )
}
```

- [ ] **Step 3: Verify in browser**

Open http://localhost:3000/arbitrage. Enter odds of +200 and +200 for a $1000 stake — should show an arb opportunity with ~$333 profit. Enter -110 and -110 — should show no arb.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/arb/ frontend/app/arbitrage/
git commit -m "feat: add Arbitrage Calculator with two-leg arb math"
```

---

## Task 9: Sharp Metrics Page

**Files:**
- Create: `frontend/components/sharp/ClvPanel.tsx`
- Create: `frontend/components/sharp/LineMovementPanel.tsx`
- Create: `frontend/app/sharp/page.tsx`

- [ ] **Step 1: Create ClvPanel**

Create `frontend/components/sharp/ClvPanel.tsx`:
```tsx
import { Bet, MOCK_BETS } from "@/lib/mock-data"

type Props = { bets: Bet[] }

export function ClvPanel({ bets }: Props) {
  const settled = bets.filter((b) => b.result !== "pending" && b.clv !== 0)
  const avgClv = settled.length > 0 ? settled.reduce((s, b) => s + b.clv, 0) / settled.length : 0
  const positive = settled.filter((b) => b.clv > 0).length

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="font-semibold">Closing Line Value (CLV)</div>
      <p className="text-xs text-muted-foreground">CLV measures how much better your bet was than the closing price. Positive CLV over a large sample indicates you are beating the market.</p>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="rounded border px-3 py-2">
          <div className="text-xs text-muted-foreground">Avg CLV</div>
          <div className={`text-xl font-bold ${avgClv >= 0 ? "text-green-600" : "text-red-500"}`}>
            {avgClv >= 0 ? "+" : ""}{avgClv.toFixed(1)}
          </div>
        </div>
        <div className="rounded border px-3 py-2">
          <div className="text-xs text-muted-foreground">Positive CLV bets</div>
          <div className="text-xl font-bold">{positive}/{settled.length}</div>
        </div>
        <div className="rounded border px-3 py-2">
          <div className="text-xs text-muted-foreground">CLV %</div>
          <div className="text-xl font-bold">
            {settled.length > 0 ? ((positive / settled.length) * 100).toFixed(0) : 0}%
          </div>
        </div>
      </div>
      <div className="space-y-1">
        {settled.map((b) => (
          <div key={b.id} className="flex justify-between text-sm py-1 border-b last:border-0">
            <span className="text-muted-foreground">{b.game} — {b.betType}</span>
            <span className={`font-medium ${b.clv > 0 ? "text-green-600" : "text-red-500"}`}>
              {b.clv > 0 ? "+" : ""}{b.clv} CLV
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create LineMovementPanel**

Create `frontend/components/sharp/LineMovementPanel.tsx`:
```tsx
const MOCK_LINE_MOVEMENT = [
  { game: "Chiefs vs Bills", betType: "Spread", open: -2.5, current: -3.5, book: "Pinnacle", steamFlag: true },
  { game: "Celtics vs Lakers", betType: "ML", open: -185, current: -200, book: "DraftKings", steamFlag: false },
  { game: "Yankees vs Red Sox", betType: "Total", open: 8.5, current: 9, book: "FanDuel", steamFlag: true },
]

export function LineMovementPanel() {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="font-semibold">Line Movement</div>
      <p className="text-xs text-muted-foreground">Lines that have moved significantly since open. Steam flag indicates rapid movement across multiple books (sharp money signal).</p>
      <div className="space-y-2">
        {MOCK_LINE_MOVEMENT.map((line) => (
          <div key={`${line.game}-${line.betType}`} className="flex items-center justify-between rounded border px-3 py-2 text-sm">
            <div>
              <span className="font-medium">{line.game}</span>
              <span className="text-muted-foreground ml-2">{line.betType}</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-muted-foreground">{line.open} → <span className="text-foreground font-medium">{line.current}</span></span>
              <span className="text-xs text-muted-foreground">{line.book}</span>
              {line.steamFlag && (
                <span className="text-xs font-medium px-2 py-0.5 rounded bg-orange-100 text-orange-700">Steam</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create Sharp Metrics page**

Create `frontend/app/sharp/page.tsx`:
```tsx
import { ClvPanel } from "@/components/sharp/ClvPanel"
import { LineMovementPanel } from "@/components/sharp/LineMovementPanel"
import { MOCK_BETS } from "@/lib/mock-data"

export default function SharpPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Sharp Metrics</h1>
        <p className="text-sm text-muted-foreground mt-1">Tools used by professional bettors to evaluate edge</p>
      </div>
      <ClvPanel bets={MOCK_BETS} />
      <LineMovementPanel />
    </div>
  )
}
```

- [ ] **Step 4: Verify in browser**

Open http://localhost:3000/sharp — should see CLV stats panel and line movement table with steam flags.

- [ ] **Step 5: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/components/sharp/ frontend/app/sharp/
git commit -m "feat: add Sharp Metrics page with CLV and line movement"
```

---

## Task 10: Auth Pages

**Files:**
- Create: `frontend/app/auth/login/page.tsx`
- Create: `frontend/app/auth/register/page.tsx`

- [ ] **Step 1: Create Login page**

Create `frontend/app/auth/login/page.tsx`:
```tsx
"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function LoginPage() {
  const [form, setForm] = useState({ email: "", password: "" })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    alert("Auth not yet connected — coming in next phase")
  }

  return (
    <div className="max-w-sm mx-auto mt-16 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Log in to OddsIQ</h1>
        <p className="text-sm text-muted-foreground mt-1">Track bets, set alerts, find edges</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border p-6">
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input type="email" placeholder="you@example.com" value={form.email} onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))} required />
        </div>
        <div className="space-y-1.5">
          <Label>Password</Label>
          <Input type="password" placeholder="••••••••" value={form.password} onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))} required />
        </div>
        <Button type="submit" className="w-full">Log in</Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        No account? <Link href="/auth/register" className="text-primary hover:underline">Sign up</Link>
      </p>
    </div>
  )
}
```

- [ ] **Step 2: Create Register page**

Create `frontend/app/auth/register/page.tsx`:
```tsx
"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function RegisterPage() {
  const [form, setForm] = useState({ email: "", password: "", confirm: "" })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (form.password !== form.confirm) {
      alert("Passwords do not match")
      return
    }
    alert("Auth not yet connected — coming in next phase")
  }

  return (
    <div className="max-w-sm mx-auto mt-16 space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Create your account</h1>
        <p className="text-sm text-muted-foreground mt-1">Free forever</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border p-6">
        <div className="space-y-1.5">
          <Label>Email</Label>
          <Input type="email" placeholder="you@example.com" value={form.email} onChange={(e) => setForm((s) => ({ ...s, email: e.target.value }))} required />
        </div>
        <div className="space-y-1.5">
          <Label>Password</Label>
          <Input type="password" placeholder="••••••••" value={form.password} onChange={(e) => setForm((s) => ({ ...s, password: e.target.value }))} required />
        </div>
        <div className="space-y-1.5">
          <Label>Confirm Password</Label>
          <Input type="password" placeholder="••••••••" value={form.confirm} onChange={(e) => setForm((s) => ({ ...s, confirm: e.target.value }))} required />
        </div>
        <Button type="submit" className="w-full">Create account</Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Already have an account? <Link href="/auth/login" className="text-primary hover:underline">Log in</Link>
      </p>
    </div>
  )
}
```

- [ ] **Step 3: Verify in browser**

Open http://localhost:3000/auth/login and http://localhost:3000/auth/register. Both forms should render and submit with an alert placeholder.

- [ ] **Step 4: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add frontend/app/auth/
git commit -m "feat: add Login and Register pages"
```

---

## Task 11: FastAPI Mock Routes

**Files:**
- Create: `backend/api/v1/odds.py`
- Create: `backend/api/v1/alerts.py`
- Create: `backend/api/v1/bets.py`
- Create: `backend/api/v1/arb.py`
- Create: `backend/api/v1/sharp.py`

- [ ] **Step 1: Create odds router**

Create `backend/api/v1/odds.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["odds"])

class BestLine(BaseModel):
    homeMoneyline: int
    awayMoneyline: int
    spread: float
    spreadOdds: int
    total: float
    overOdds: int
    underOdds: int
    book: str

class Game(BaseModel):
    id: str
    sport: str
    homeTeam: str
    awayTeam: str
    commenceTime: str
    bestLine: BestLine

MOCK_GAMES = [
    Game(id="1", sport="NFL", homeTeam="Kansas City Chiefs", awayTeam="Buffalo Bills",
         commenceTime="2026-09-10T20:20:00Z",
         bestLine=BestLine(homeMoneyline=-150, awayMoneyline=130, spread=-3, spreadOdds=-110,
                           total=47.5, overOdds=-110, underOdds=-110, book="DraftKings")),
]

@router.get("/odds", response_model=list[Game])
def get_odds(sport: str | None = None):
    if sport:
        return [g for g in MOCK_GAMES if g.sport == sport]
    return MOCK_GAMES
```

- [ ] **Step 2: Create alerts router**

Create `backend/api/v1/alerts.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["alerts"])

class AlertCreate(BaseModel):
    game: str
    betType: str
    targetOdds: int
    book: str

class Alert(AlertCreate):
    id: str
    status: str
    createdAt: str

_alerts: list[Alert] = []

@router.get("/alerts", response_model=list[Alert])
def list_alerts():
    return _alerts

@router.post("/alerts", response_model=Alert, status_code=201)
def create_alert(body: AlertCreate):
    alert = Alert(id=str(len(_alerts) + 1), status="active", createdAt="2026-05-29", **body.model_dump())
    _alerts.append(alert)
    return alert

@router.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: str):
    global _alerts
    _alerts = [a for a in _alerts if a.id != alert_id]
```

- [ ] **Step 3: Create bets router**

Create `backend/api/v1/bets.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["bets"])

class BetCreate(BaseModel):
    date: str
    sport: str
    game: str
    betType: str
    odds: int
    stake: float
    result: str

class Bet(BetCreate):
    id: str
    pnl: float
    closingOdds: int
    clv: float

_bets: list[Bet] = []

@router.get("/bets", response_model=list[Bet])
def list_bets():
    return _bets

@router.post("/bets", response_model=Bet, status_code=201)
def create_bet(body: BetCreate):
    bet = Bet(id=str(len(_bets) + 1), pnl=0.0, closingOdds=body.odds, clv=0.0, **body.model_dump())
    _bets.append(bet)
    return bet
```

- [ ] **Step 4: Create arb router**

Create `backend/api/v1/arb.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["arb"])

class ArbRequest(BaseModel):
    leg1Odds: int
    leg2Odds: int
    totalStake: float

class ArbResult(BaseModel):
    impliedProb: float
    isArb: bool
    stake1: float
    stake2: float
    profit: float

def american_to_decimal(odds: int) -> float:
    if odds > 0:
        return odds / 100 + 1
    return 100 / abs(odds) + 1

@router.post("/arb/calculate", response_model=ArbResult)
def calculate_arb(body: ArbRequest):
    d1 = american_to_decimal(body.leg1Odds)
    d2 = american_to_decimal(body.leg2Odds)
    implied = 1 / d1 + 1 / d2
    is_arb = implied < 1
    stake1 = (body.totalStake / d1) / implied
    stake2 = (body.totalStake / d2) / implied
    profit = body.totalStake * (1 / implied - 1) if is_arb else 0
    return ArbResult(impliedProb=implied, isArb=is_arb, stake1=stake1, stake2=stake2, profit=profit)
```

- [ ] **Step 5: Create sharp router**

Create `backend/api/v1/sharp.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["sharp"])

class LineMovement(BaseModel):
    game: str
    betType: str
    openLine: float
    currentLine: float
    book: str
    steamFlag: bool

@router.get("/sharp/line-movement", response_model=list[LineMovement])
def get_line_movement():
    return [
        LineMovement(game="Chiefs vs Bills", betType="Spread", openLine=-2.5, currentLine=-3.5, book="Pinnacle", steamFlag=True),
        LineMovement(game="Celtics vs Lakers", betType="ML", openLine=-185, currentLine=-200, book="DraftKings", steamFlag=False),
    ]
```

- [ ] **Step 6: Verify all routes with FastAPI docs**

```bash
cd /Users/lucassimon/OddsIQ/backend
uv run uvicorn main:app --reload
```

Open http://localhost:8000/docs — should see all routes: `/api/v1/odds`, `/api/v1/alerts`, `/api/v1/bets`, `/api/v1/arb/calculate`, `/api/v1/sharp/line-movement`. Test each one using the interactive docs.

- [ ] **Step 7: Commit**

```bash
cd /Users/lucassimon/OddsIQ
git add backend/
git commit -m "feat: add FastAPI mock routes for all resources"
```

---

## Task 12: Final Smoke Test

- [ ] **Step 1: Run frontend and backend together**

Terminal 1:
```bash
cd /Users/lucassimon/OddsIQ/backend
uv run uvicorn main:app --reload --port 8000
```

Terminal 2:
```bash
cd /Users/lucassimon/OddsIQ/frontend
pnpm dev
```

- [ ] **Step 2: Walk all pages**

Visit each route and confirm it loads without errors:
- http://localhost:3000 — Odds Board with sport filters
- http://localhost:3000/line-shopping — Book comparison table
- http://localhost:3000/alerts — Alert list + create form
- http://localhost:3000/pnl — Stat cards + bet log + bet form
- http://localhost:3000/arbitrage — Arb calculator (test +200/+200 case)
- http://localhost:3000/sharp — CLV panel + line movement
- http://localhost:3000/auth/login — Login form
- http://localhost:3000/auth/register — Register form

- [ ] **Step 3: Final commit**

```bash
cd /Users/lucassimon/OddsIQ
git add .
git commit -m "chore: complete skeleton — all pages and API routes wired"
```
