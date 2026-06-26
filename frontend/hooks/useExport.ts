'use client'
import { useCallback } from 'react'
import { getExportUrl } from '@/lib/api'

export function useExport() {
  const downloadSketch = useCallback((sessionId: string) => {
    window.open(getExportUrl(sessionId, 'sketch'), '_blank')
  }, [])

  const downloadCircuit = useCallback((sessionId: string) => {
    window.open(getExportUrl(sessionId, 'circuit'), '_blank')
  }, [])

  return { downloadSketch, downloadCircuit }
}
