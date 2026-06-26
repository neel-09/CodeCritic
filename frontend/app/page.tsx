'use client'
import { useState, KeyboardEvent } from 'react'
import { useRouter } from 'next/navigation'
import { BOARDS, getBoardByName } from '@/lib/boards'
import SupportedComponentsPanel from "@/components/SupportedComponentsPanel";
import { SUPPORTED_COMPONENTS } from '@/lib/supportedComponents'

const BOARD_COLORS: Record<string, string> = {
  'Arduino Uno':     '#0d3a6e',
  'Arduino Nano':    '#0d3a6e',
  'Arduino Mega':    '#0d3a6e',
}

const EXAMPLES = [
  'Blink LED every 500ms on pin 13',
]

const STEPS = [
  { label: 'Plan',    color: '#6366f1' },
  { label: 'Code',    color: '#14b8a6' },
  { label: 'Circuit', color: '#f59e0b' },
  { label: 'Verify',  color: '#22c55e' },
]

export default function HomePage() {
  const router = useRouter()
  const [prompt, setPrompt]   = useState('')
  const [board, setBoard]     = useState(BOARDS[0].name)
  const [fqbn, setFqbn]       = useState(BOARDS[0].fqbn)
  const [focused, setFocused] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const [unknownComponent, setUnknownComponent] = useState<string | null>(null)

  const handleBoardChange = (value: string) => {
    const b = getBoardByName(value)
    if (b) { setBoard(b.name); setFqbn(b.fqbn) }
  }

  const checkForUnknownComponents = (text: string): string | null => {
    const flat = Object.values(SUPPORTED_COMPONENTS)
      .flat()
      .map(c => c.name.toLowerCase())

    const tokens = text.match(/\b[A-Za-z][A-Za-z0-9]*[0-9][A-Za-z0-9]*\b|\b[A-Z]{2,}\b|\b[A-Z][a-z]+[A-Z][a-zA-Z]*\b/g) ?? []

    for (const token of tokens) {
      const t = token.toLowerCase()
      const matched = flat.some(name => name.includes(t) || t.includes(name.split(' ')[0]))
      if (!matched) return token
    }
    return null
  }

  const handleSubmit = () => {
    if (!prompt.trim()) return
    const unknown = checkForUnknownComponents(prompt)
    if (unknown) { setUnknownComponent(unknown); return }
    setLeaving(true)
    setTimeout(() => {
      const params = new URLSearchParams({ prompt: prompt.trim(), board, fqbn })
      router.push(`/generate?${params.toString()}`)
    }, 380)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.ctrlKey && e.key === 'Enter') handleSubmit()
  }

  return (
    <div
      className="h-screen bg-[#040d08] text-white flex flex-col overflow-hidden"
      style={{ transition: 'opacity 0.38s ease, transform 0.38s ease',
               opacity: leaving ? 0 : 1,
               transform: leaving ? 'scale(0.98)' : 'scale(1)' }}
    >
      {/* Grid bg */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: `linear-gradient(rgba(20,184,166,0.025) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(20,184,166,0.025) 1px, transparent 1px)`,
        backgroundSize: '48px 48px',
      }} />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[220px] pointer-events-none"
           style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(20,184,166,0.07) 0%, transparent 70%)' }} />

      {/* Nav */}
      <nav className="relative flex items-center justify-between px-8 py-4 border-b border-white/5 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <span className="font-mono font-semibold tracking-tight">CodeCritic</span>
        </div>
        <div className="flex items-center gap-4">
          {STEPS.map((s, i) => (
            <div key={s.label} className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse"
                   style={{ backgroundColor: s.color, animationDelay: `${i * 0.4}s` }} />
              <span className="text-[10px] font-mono text-white/60 tracking-widest uppercase">{s.label}</span>
            </div>
          ))}
        </div>
      </nav>

      {/* Body — two columns */}
      <div className="relative flex-1 flex items-stretch overflow-hidden">

        {/* Left */}
        <div className="flex flex-col justify-center px-14 w-[44%] flex-shrink-0">
          <h1 className="text-[2.6rem] font-bold leading-[1.15] tracking-tight mb-5">
            Arduino code
            <br />
            <span className="text-teal-400">that works</span>
            <br />
            before you build
          </h1>

          <p className="text-white/70 text-base leading-relaxed mb-8 max-w-sm">
            Describe your embedded system in plain English.
            Get verified code and a wired circuit diagram —
            compiled and simulated.
          </p>
        </div>

        {/* Divider */}
        <div className="w-px bg-zinc-900 flex-shrink-0 my-8" />

        {/* Right — form */}
        <div className="flex-1 flex flex-col justify-center px-12">
          <div className={`rounded-2xl border transition-all duration-300 bg-zinc-900/90 backdrop-blur-sm
                          ring-1 ring-white/5 shadow-2xl shadow-black/50
                          ${focused ? 'border-teal-500/35 shadow-[0_0_0_3px_rgba(20,184,166,0.05)]'
                                    : 'border-zinc-700/60'}`}>

            <div className="px-5 pt-5 pb-4 border-b border-zinc-800/60">
              <p className="text-[10px] font-mono text-white/60 uppercase tracking-widest mb-3">Target board</p>
              <div className="flex flex-wrap gap-2">
                {BOARDS.map(b => {
                  const sel = b.name === board
                  return (
                    <button key={b.fqbn} type="button" onClick={() => handleBoardChange(b.name)}
                            className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-mono
                                        transition-all border
                              ${sel ? 'border-teal-600/50 bg-teal-950/60 text-teal-300'
                                    : 'border-zinc-800 bg-zinc-900/40 text-white/70 hover:border-zinc-700 hover:text-white'}`}>
                      <span className="w-2 h-2 rounded-sm"
                            style={{ backgroundColor: sel ? '#2dd4bf' : (BOARD_COLORS[b.name] ?? '#333') }} />
                      {b.name}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="px-5 pt-4 pb-2">
              <p className="text-[10px] font-mono text-white/60 uppercase tracking-widest mb-3">What should it do?</p>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                placeholder="e.g. Read humidity from DHT22 and display on LCD every 2 seconds"
                rows={3}
                className="w-full bg-transparent text-white text-sm leading-relaxed
                           focus:outline-none resize-none placeholder:text-white/40 font-sans"
              />
            </div>

            <div className="px-5 pb-4">
              <div className="flex flex-wrap gap-1.5">
                {EXAMPLES.map(ex => (
                  <button key={ex} type="button" onClick={() => setPrompt(ex)}
                          className="text-[10px] px-2 py-1 rounded-md border border-zinc-800/80
                                     text-white/60 hover:text-white hover:border-zinc-700
                                     transition-colors font-mono">
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            <div className="px-5 pb-4">
              <SupportedComponentsPanel />
            </div>

            <div className="px-5 pb-5">
              <button onClick={handleSubmit} disabled={!prompt.trim()}
                      className="w-full py-3 rounded-xl font-semibold text-sm tracking-wide
                                 bg-teal-500 hover:bg-teal-400 text-zinc-950
                                 disabled:opacity-25 disabled:cursor-not-allowed
                                 active:scale-[0.99] transition-all duration-150
                                 flex items-center justify-center gap-2">
                Generate Code & Circuit
                <span className="opacity-50 font-mono font-normal text-xs">⌃↵</span>
              </button>
            </div>
          </div>

          <p className="text-center text-[10px] text-white/50 font-mono mt-4">
            compiled with arduino-cli · simulated with wokwi-cli
          </p>
        </div>
      </div>

      {/* Unknown component modal */}
      {unknownComponent && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-zinc-900 border border-zinc-700/60 ring-1 ring-white/5 rounded-2xl
                          shadow-2xl shadow-black/50 p-8 max-w-sm w-full mx-4 flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <span className="text-xs font-mono text-amber-400 uppercase tracking-widest">Unsupported Component</span>
              <p className="text-white/90 text-sm leading-relaxed">
                <span className="font-mono text-white">"{unknownComponent}"</span> is not in the supported components list.
                Check the supported components panel and adjust your prompt.
              </p>
            </div>
            <button
              onClick={() => setUnknownComponent(null)}
              className="w-full py-2.5 rounded-xl font-semibold text-sm bg-zinc-800
                         hover:bg-zinc-700 text-white/90 transition-all border border-zinc-700/60">
              Edit Prompt
            </button>
          </div>
        </div>
      )}
    </div>
  )
}