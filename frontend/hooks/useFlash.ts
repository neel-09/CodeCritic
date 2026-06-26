import { useState, useCallback } from 'react'
import { flashHex, FlashStatus } from '@/lib/Stk500'

export function useFlash(sessionId: string, board: string) {
  const [status, setStatus]     = useState<FlashStatus>('idle')
  const [progress, setProgress] = useState(0)
  const [error, setError]       = useState<string | null>(null)

  const flash = useCallback(async () => {
    setError(null)
    setProgress(0)

    try {
      // Fetch hex from backend
      const res = await fetch(`/api/hex/${sessionId}`)
      if (!res.ok) throw new Error('Failed to fetch firmware')
      const hexText = await res.text()

      await flashHex(hexText, board, setStatus, setProgress)
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Flash failed')
    }
  }, [sessionId, board])

  const reset = useCallback(() => {
    setStatus('idle')
    setProgress(0)
    setError(null)
  }, [])

  return { flash, reset, status, progress, error }
}