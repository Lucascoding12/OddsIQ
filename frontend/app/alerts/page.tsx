"use client"
import { ProtectedRoute } from "@/components/ProtectedRoute"

import { useState } from "react"
import { AlertList } from "@/components/alerts/AlertList"
import { AlertForm } from "@/components/alerts/AlertForm"
import { Alert } from "@/lib/mock-data"

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])

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
    <ProtectedRoute>
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Alerts</h1>
        <p className="text-sm text-muted-foreground mt-1">Get notified when a line hits your target</p>
      </div>
      <AlertList alerts={alerts} onDelete={handleDelete} />
      <AlertForm onSubmit={handleCreate} />
    </div>
    </ProtectedRoute>
  )
}