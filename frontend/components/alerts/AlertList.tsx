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
