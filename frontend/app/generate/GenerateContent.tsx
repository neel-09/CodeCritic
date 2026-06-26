'use client'
import { useEffect, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useGeneration, VISIBLE_NODES, NODE_LABELS } from '@/hooks/useGeneration'

export default function GenerateContent() {
  const router = useRouter()
  const params = useSearchParams()
  const prompt = params.get('prompt') || ''
  const board  = params.get('board')  || ''
  const fqbn   = params.get('fqbn')   || ''
  const hasStarted = useRef(false)

  const { status, nodes, result, clarificationQuestion, error, activeNode, generate } = useGeneration()

  useEffect(() => {
    if (hasStarted.current || !prompt || !fqbn) return
    hasStarted.current = true
    generate(prompt, board, fqbn)
  }, [prompt, board, fqbn, generate])

  useEffect(() => {
    if (status === 'done' && result) {
      sessionStorage.setItem('codecritic_result', JSON.stringify({ result, board, prompt }))
      router.push('/result')
    }
  }, [status, result, board, prompt, router])

  const visibleCompleted = VISIBLE_NODES.filter(n => nodes[n] === 'complete').length
  const progress = Math.round((visibleCompleted / VISIBLE_NODES.length) * 100)

  return (
    <div className="min-h-screen bg-[#050505] text-white flex">

      {/* Left panel — pipeline */}
      <div className="w-[380px] flex-shrink-0 border-r border-[#111] p-8 flex flex-col gap-8">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.15em] text-zinc-600 uppercase mb-6">
            Processing Pipeline
          </p>
          <div className="space-y-0.5">
            {VISIBLE_NODES.map(node => {
              const s = nodes[node] || 'pending'
              return (
                <div key={node} className="flex items-center gap-4 py-2.5">
                  {/* Status circle */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all
                    ${s === 'complete' ? 'bg-teal-700' :
                      s === 'running'  ? 'border-2 border-teal-600' :
                                         'border-2 border-[#1f1f1f]'}`}
                  >
                    {s === 'complete' && (
                      <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {s === 'running' && (
                      <div className="w-2.5 h-2.5 rounded-full bg-teal-500 animate-pulse" />
                    )}
                  </div>
                  {/* Label */}
                  <div>
                    <p className={`text-sm font-medium transition-colors
                      ${s === 'complete' ? 'text-white' :
                        s === 'running'  ? 'text-teal-400' :
                                           'text-zinc-700'}`}
                    >
                      {NODE_LABELS[node]}
                    </p>
                    {s === 'running' && (
                      <p className="text-[11px] text-teal-700 mt-0.5">Running...</p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Request details */}
        <div className="bg-[#0a0a0a] border border-[#111] rounded-lg p-4">
          <p className="text-[10px] font-semibold tracking-[0.15em] text-zinc-600 uppercase mb-3">
            Request Details
          </p>
          <div className="space-y-3">
            <div>
              <p className="text-[11px] text-teal-700 mb-0.5">Target Board</p>
              <p className="text-sm text-zinc-300">{board || '—'}</p>
            </div>
            <div>
              <p className="text-[11px] text-teal-700 mb-0.5">Prompt</p>
              <p className="text-sm text-zinc-400 leading-relaxed">{prompt || '—'}</p>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-950/40 border border-red-900 rounded-lg p-4">
            <p className="text-[10px] font-semibold text-red-500 uppercase tracking-wider mb-1">Error</p>
            <p className="text-sm text-red-300 leading-relaxed">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-3 text-xs text-red-400 hover:text-red-300 underline"
            >
              ← Back to home
            </button>
          </div>
        )}

        {/* Clarification */}
        {status === 'clarification' && clarificationQuestion && (
          <ClarificationBox
            question={clarificationQuestion}
            originalPrompt={prompt}
            board={board}
            fqbn={fqbn}
            onSubmit={generate}
          />
        )}
      </div>

      {/* Right panel — code preview */}
      <div className="flex-1 p-8">
        <p className="text-[10px] font-semibold tracking-[0.15em] text-zinc-600 uppercase mb-6">
          Code Generation
        </p>

        <div className="bg-[#0a0a0a] border border-[#111] rounded-lg overflow-hidden">
          {/* Code header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-[#111]">
            <span className="text-xs font-mono text-teal-600">sketch.ino</span>
            <span className="text-xs text-zinc-700">{progress}%</span>
          </div>

          {/* Skeleton code lines */}
          <div className="p-5 space-y-2.5">
            {[80, 55, 0, 65, 40, 90, 0, 75, 50, 45, 70, 60].map((w, i) => (
              w === 0
                ? <div key={i} className="h-4" />
                : <div
                    key={i}
                    className="h-3.5 rounded bg-[#141414] skeleton"
                    style={{ width: `${w}%`, animationDelay: `${i * 80}ms` }}
                  />
            ))}
          </div>

          {/* Progress bar */}
          <div className="h-0.5 bg-[#111]">
            <div
              className="h-full bg-teal-700 transition-all duration-700 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Status */}
        <div className="mt-4 flex items-center gap-2 h-5">
          {activeNode && (
            <>
              <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
              <span className="text-xs text-zinc-500">
                {NODE_LABELS[activeNode] || activeNode} in progress...
              </span>
            </>
          )}
          {status === 'error' && (
            <>
              <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
              <span className="text-xs text-red-500">Generation failed</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function ClarificationBox({
  question, originalPrompt, board, fqbn, onSubmit
}: {
  question: string
  originalPrompt: string
  board: string
  fqbn: string
  onSubmit: (prompt: string, board: string, fqbn: string) => void
}) {
  const [answer, setAnswer] = useState('')

  const handleSubmit = () => {
    if (!answer.trim()) return
    onSubmit(`${originalPrompt}. clarification: ${answer.trim()}`, board, fqbn)
  }

  return (
    <div className="bg-[#0a0a0a] border border-teal-900 rounded-lg p-4">
      <p className="text-[10px] font-semibold text-teal-600 uppercase tracking-wider mb-2">
        Clarification needed
      </p>
      <p className="text-sm text-zinc-300 leading-relaxed mb-3">{question}</p>
      <input
        type="text"
        value={answer}
        onChange={e => setAnswer(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && handleSubmit()}
        placeholder="Your answer..."
        autoFocus
        className="w-full bg-[#111] border border-[#1f1f1f] text-white rounded px-3 py-2 text-sm
                   focus:outline-none focus:border-teal-700 transition-colors placeholder:text-zinc-700 mb-2"
      />
      <button
        onClick={handleSubmit}
        className="w-full bg-teal-800 hover:bg-teal-700 text-white text-sm py-2 rounded transition-colors"
      >
        Continue
      </button>
    </div>
  )
}
