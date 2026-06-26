'use client'
import { useFlash } from '@/hooks/useFlash'

const STATUS_LABEL: Record<string, string> = {
  idle:       'Deploy to Board',
  connecting: 'Connecting...',
  resetting:  'Resetting...',
  flashing:   'Flashing...',
  done:       'Done!',
  error:      'Failed',
}

const STATUS_COLOR: Record<string, string> = {
  idle:       'bg-teal-500 hover:bg-teal-400 text-zinc-950',
  connecting: 'bg-zinc-700 text-white/70 cursor-wait',
  resetting:  'bg-zinc-700 text-white/70 cursor-wait',
  flashing:   'bg-zinc-700 text-white/70 cursor-wait',
  done:       'bg-green-600 text-white cursor-default',
  error:      'bg-red-600/80 text-white',
}

const isChromium = () =>
  typeof navigator !== 'undefined' && 'serial' in navigator

interface DeployButtonProps {
  sessionId: string
  board: string
}

export default function DeployButton({ sessionId, board }: DeployButtonProps) {
  const { flash, reset, status, progress, error } = useFlash(sessionId, board)

  if (!isChromium()) {
    return (
      <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-zinc-700/60
                      bg-zinc-900/60 text-white/40 text-sm font-mono">
        <span className="text-[10px] uppercase tracking-widest">Deploy unavailable</span>
        <span className="text-[10px] text-white/30">· requires Chrome or Edge</span>
      </div>
    )
  }

  const busy = ['connecting', 'resetting', 'flashing'].includes(status)

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={status === 'error' ? reset : status === 'idle' ? flash : undefined}
        disabled={busy || status === 'done'}
        className={`flex items-center justify-center gap-2.5 px-5 py-2.5 rounded-xl
                    font-semibold text-sm tracking-wide transition-all duration-150
                    disabled:cursor-not-allowed active:scale-[0.99]
                    ${STATUS_COLOR[status]}`}
      >
        {/* Icon */}
        {status === 'done' ? (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        ) : status === 'error' ? (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4l16 16M4 20L20 4" />
          </svg>
        ) : (
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m-7 7l7-7 7 7" />
          </svg>
        )}

        {STATUS_LABEL[status]}

        {/* Progress percentage while flashing */}
        {status === 'flashing' && (
          <span className="font-mono text-xs text-white/60">{progress}%</span>
        )}
      </button>

      {/* Progress bar */}
      {status === 'flashing' && (
        <div className="h-1 w-full rounded-full bg-zinc-800 overflow-hidden">
          <div
            className="h-full bg-teal-500 rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Error message */}
      {status === 'error' && error && (
        <p className="text-xs font-mono text-red-400/80">{error} · click to retry</p>
      )}

      {/* Board label */}
      {status === 'idle' && (
        <p className="text-[10px] font-mono text-white/30 text-center">
          plug in {board} via USB before clicking
        </p>
      )}
    </div>
  )
}