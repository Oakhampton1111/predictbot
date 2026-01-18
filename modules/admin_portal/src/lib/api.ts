const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''
const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8080'

// Orchestrator API client
export const orchestratorApi = {
  async getDashboard() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/dashboard`)
    if (!res.ok) return null
    return res.json()
  },

  async getStrategies() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/strategies`)
    if (!res.ok) return []
    return res.json()
  },

  async toggleStrategy(strategyId: string, enabled: boolean) {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/strategies/${strategyId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled }),
    })
    if (!res.ok) throw new Error('Failed to toggle strategy')
    return res.json()
  },

  async getPositions() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/positions`)
    if (!res.ok) return []
    return res.json()
  },

  async closePosition(positionId: string) {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/positions/${positionId}/close`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to close position')
    return res.json()
  },

  async getConfig() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/config`)
    if (!res.ok) return null
    return res.json()
  },

  async updateConfig(config: any) {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    if (!res.ok) throw new Error('Failed to update config')
    return res.json()
  },

  async emergencyStop() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/emergency/stop`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to execute emergency stop')
    return res.json()
  },

  async emergencyResume() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/emergency/resume`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to resume')
    return res.json()
  },

  async emergencyPause() {
    const res = await fetch(`${ORCHESTRATOR_URL}/api/emergency/pause`, {
      method: 'POST',
    })
    if (!res.ok) throw new Error('Failed to pause')
    return res.json()
  },

  async getHealth() {
    const res = await fetch(`${ORCHESTRATOR_URL}/health`)
    if (!res.ok) return { status: 'unhealthy' }
    return res.json()
  },
}

// Legacy function exports for backward compatibility
export async function fetchDashboard() {
  const res = await fetch(`${API_BASE}/api/dashboard`)
  if (!res.ok) throw new Error('Failed to fetch dashboard')
  return res.json()
}

export async function fetchPositions() {
  const res = await fetch(`${API_BASE}/api/positions`)
  if (!res.ok) throw new Error('Failed to fetch positions')
  return res.json()
}

export async function fetchStrategies() {
  const res = await fetch(`${API_BASE}/api/strategies`)
  if (!res.ok) throw new Error('Failed to fetch strategies')
  return res.json()
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health/detailed`)
  if (!res.ok) throw new Error('Failed to fetch health')
  return res.json()
}

export async function fetchConfig() {
  const res = await fetch(`${API_BASE}/api/config`)
  if (!res.ok) throw new Error('Failed to fetch config')
  return res.json()
}

export async function updateConfig(config: any) {
  const res = await fetch(`${API_BASE}/api/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!res.ok) throw new Error('Failed to update config')
  return res.json()
}

export async function fetchAlerts() {
  const res = await fetch(`${API_BASE}/api/alerts`)
  if (!res.ok) throw new Error('Failed to fetch alerts')
  return res.json()
}

export async function fetchTrades() {
  const res = await fetch(`${API_BASE}/api/trades`)
  if (!res.ok) throw new Error('Failed to fetch trades')
  return res.json()
}

export async function executeTrade(trade: any) {
  const res = await fetch(`${API_BASE}/api/trade`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(trade),
  })
  if (!res.ok) throw new Error('Failed to execute trade')
  return res.json()
}

export async function emergencyStop() {
  const res = await fetch(`${API_BASE}/api/emergency`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'stop' }),
  })
  if (!res.ok) throw new Error('Failed to execute emergency stop')
  return res.json()
}
