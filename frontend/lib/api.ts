const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface GenerateRequest {
  prompt: string
  board: string
  fqbn: string
}

export interface GenerateResult {
  sketch_ino: string
  diag_json: string
  pass_score: number
  assertion_diff: Record<string, unknown>
  session_id: string
}

export interface SSEEvent {
  type: 'node_start' | 'node_complete' | 'clarification' | 'error' | 'done'
  node?: string
  question?: string
  message?: string
  result?: GenerateResult
}

export async function streamGenerate(
  req: GenerateRequest,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(`${API_BASE}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal,
  })
}

export function getExportUrl(sessionId: string, type: 'sketch' | 'circuit') {
  return `${API_BASE}/export/${sessionId}/${type}`
}
