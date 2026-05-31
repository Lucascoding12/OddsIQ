"use client"

import { useState, useEffect } from "react"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { AlertList } from "@/components/alerts/AlertList"
import { AlertForm } from "@/components/alerts/AlertForm"
import { getAlerts, createAlert, deleteAlert, type Alert, type AlertCreate } from "@/lib/api"

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAlerts()
      .then(setAlerts)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(data: AlertCreate) {
    const newAlert = await createAlert(data)
    setAlerts((prev) => [newAlert, ...prev])
  }

  async function handleDelete(id: number) {
    await deleteAlert(id)
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Price <span className="text-primary">Alerts</span></h1>
          <p className="text-sm text-muted-foreground mt-1">Get notified when a line hits your target</p>
        </div>
        {loading ? (
          <p className="text-sm text-muted-foreground animate-pulse">Loading alerts…</p>
        ) : (
          <AlertList alerts={alerts} onDelete={handleDelete} />
        )}
        <AlertForm onSubmit={handleCreate} />
      </div>
    </ProtectedRoute>
  )
}
