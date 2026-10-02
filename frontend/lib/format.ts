/** Shared display formatting for odds, probabilities, and game times. */

export function formatOdds(odds: number | null | undefined): string {
  if (odds == null) return "—"
  return odds > 0 ? `+${odds}` : `${odds}`
}

/** Implied win probability of American odds, as a 0–100 percentage. */
export function impliedPct(american: number): number {
  if (american > 0) return (100 / (american + 100)) * 100
  return (Math.abs(american) / (Math.abs(american) + 100)) * 100
}

export function formatGameTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    })
  } catch {
    return iso
  }
}

export function formatClockTime(date: Date): string {
  return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit", second: "2-digit" })
}

export function formatMoney(amount: number): string {
  const sign = amount < 0 ? "-" : ""
  return `${sign}$${Math.abs(amount).toFixed(2)}`
}

export function formatSignedMoney(amount: number): string {
  return `${amount >= 0 ? "+" : "-"}$${Math.abs(amount).toFixed(2)}`
}
