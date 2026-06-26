'use client'
import { useState, useCallback, useRef } from 'react'
import { streamGenerate, SSEEvent, GenerateResult } from '@/lib/api'

export type NodeStatus = 'pending' | 'running' | 'complete'
export type GenerationStatus = 'idle' | 'streaming' | 'clarification' | 'done' | 'error'

export const VISIBLE_NODES = [
  'Reset',
  'Planner',
  'Coder',
  'Circuit_Designer',
  'Compiler',
  'Inspector',
  'Output',
]

export const NODE_LABELS: Record<string, string> = {
  Reset:            'Reset',
  Planner:          'Planner',
  Coder:            'Coder',
  Circuit_Designer: 'Circuit Designer',
  Compiler:         'Compiler',
  Inspector:        'Inspector',
  Output:           'Output',
}

export interface GenerationState {
  status: GenerationStatus
  nodes: Record<string, NodeStatus>
  result: GenerateResult | null
  clarificationQuestion: string | null
  error: string | null
  activeNode: string | null
}

export function useGeneration() {
  const [state, setState] = useState<GenerationState>({
    status: 'idle',
    nodes: {},
    result: null,
    clarificationQuestion: null,
    error: null,
    activeNode: null,
  })
  const abortRef = useRef<AbortController | null>(null)

  function handleEvent(event: SSEEvent) {
    setState(prev => {
      switch (event.type) {
        case 'node_start':
          return { ...prev, nodes: { ...prev.nodes, [event.node!]: 'running' }, activeNode: event.node! }
        case 'node_complete':
          return { ...prev, nodes: { ...prev.nodes, [event.node!]: 'complete' }, activeNode: null }
        case 'clarification':
          return { ...prev, status: 'clarification', clarificationQuestion: event.question ?? null }
        case 'error':
          return { ...prev, status: 'error', error: event.message ?? 'Unknown error' }
        case 'done':
          return { ...prev, status: 'done', result: event.result ?? null }
        default:
          return prev
      }
    })
  }

  const generate = useCallback(async (prompt: string, board: string, fqbn: string) => {
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setState({
      status: 'streaming',
      nodes: {},
      result: null,
      clarificationQuestion: null,
      error: null,
      activeNode: null,
    })

    try {
      const response = await streamGenerate({ prompt, board, fqbn }, abortRef.current.signal)
      if (!response.body) throw new Error('No response body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try { handleEvent(JSON.parse(line.slice(6))) } catch { /* skip */ }
        }
      }
    } catch (e) {
      if ((e as Error).name === 'AbortError') return
      setState(prev => ({
        ...prev,
        status: 'error',
        error: e instanceof Error ? e.message : 'Unknown error',
      }))
    }
  }, [])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setState(prev => ({ ...prev, status: 'idle' }))
  }, [])

  return { ...state, generate, abort }
}
