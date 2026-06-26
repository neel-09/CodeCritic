'use client'
import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { GenerateResult } from '@/lib/api'
import { useExport } from '@/hooks/useExport'
import CircuitViewer, { CircuitViewerHandle } from '@/components/CircuitViewer'
import DeployButton from '@/components/DeployButton'

interface StoredResult { result: GenerateResult; board: string; prompt: string }
interface BOMEntry { component: string; qty: number; specs: string }

const TYPE_NAMES: Record<string, string> = {
  'wokwi-arduino-uno':     'Arduino Uno',
  'wokwi-arduino-nano':    'Arduino Nano',
  'wokwi-arduino-mega':    'Arduino Mega',
  'wokwi-esp32-devkit-v1': 'ESP32 DevKit v1',
  'wokwi-led':             'LED',
  'wokwi-resistor':        'Resistor',
  'wokwi-pushbutton':      'Push Button',
  'wokwi-dht22':           'DHT22 Sensor',
  'wokwi-dht11':           'DHT11 Sensor',
  'wokwi-hc-sr04':         'Ultrasonic HC-SR04',
  'wokwi-lcd1602':         'LCD 16x2',
  'wokwi-lcd2004':         'LCD 20x4',
  'wokwi-buzzer':          'Buzzer',
  'wokwi-potentiometer':   'Potentiometer',
  'wokwi-servo':           'Servo Motor',
  'wokwi-neopixel':        'NeoPixel LED',
  'board-ssd1306':         'OLED SSD1306',
  'wokwi-mpu6050':         'MPU6050 IMU',
}

const SKIP = new Set(['wokwi-logic-analyzer'])

function parseBOM(diag_json: string): BOMEntry[] {
  try {
    const { parts = [] } = JSON.parse(diag_json)
    const map = new Map<string, { qty: number; specs: string }>()
    for (const part of parts) {
      if (SKIP.has(part.type)) continue
      const name = TYPE_NAMES[part.type] || part.type.replace('wokwi-', '').replace('board-', '')
      let specs = ''
      if (part.type === 'wokwi-resistor' && part.attrs?.value) specs = `${part.attrs.value}Ω`
      if (part.type === 'wokwi-led' && part.attrs?.color) specs = part.attrs.color
      const ex = map.get(name)
      ex ? ex.qty++ : map.set(name, { qty: 1, specs })
    }
    return [...map.entries()].map(([component, { qty, specs }]) => ({ component, qty, specs }))
  } catch { return [] }
}

function ScoreBadge({ score }: { score: number }) {
  if (score >= 0.75) return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                     bg-teal-950 border border-teal-800 text-teal-400 text-xs font-mono font-semibold">
      <span className="w-1.5 h-1.5 rounded-full bg-teal-400" /> PASS
    </span>
  )
  if (score >= 0.4) return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                     bg-amber-950 border border-amber-800 text-amber-400 text-xs font-mono font-semibold">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400" /> PARTIAL
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                     bg-red-950 border border-red-900 text-red-400 text-xs font-mono font-semibold">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400" /> FAIL
    </span>
  )
}

function CheckRow({ label, pass }: { label: string; pass: boolean }) {
  return (
    <div className="flex items-center gap-2.5 py-2 border-b border-zinc-900 last:border-0">
      <div className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0
                      ${pass ? 'bg-teal-950 border border-teal-800' : 'bg-red-950 border border-red-900'}`}>
        {pass
          ? <svg className="w-2.5 h-2.5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          : <svg className="w-2.5 h-2.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
        }
      </div>
      <span className="text-xs text-white/80 font-mono">{label}</span>
    </div>
  )
}

export default function ResultPage() {
  const router = useRouter()
  const [stored, setStored]   = useState<StoredResult | null>(null)
  const [copied, setCopied]   = useState(false)
  const [visible, setVisible] = useState(false)
  const { downloadSketch }    = useExport()
  const circuitRef            = useRef<CircuitViewerHandle>(null)

  useEffect(() => {
    const raw = sessionStorage.getItem('codecritic_result')
    if (!raw) { router.push('/'); return }
    setStored(JSON.parse(raw))
    // fade in
    requestAnimationFrame(() => requestAnimationFrame(() => setVisible(true)))
  }, [router])

  if (!stored) return (
    <div className="h-screen bg-[#060608] flex items-center justify-center">
      <div className="w-5 h-5 rounded-full border-2 border-teal-500 border-t-transparent animate-spin" />
    </div>
  )

  const { result, board, prompt } = stored
  const bom = parseBOM(result.diag_json)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.sketch_ino)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const checks = [
    { label: 'Compiled successfully', pass: result.pass_score > 0 },
    { label: 'Board compatible',      pass: result.pass_score > 0 },
    { label: 'Simulation passed',     pass: result.pass_score >= 0.75 },
  ]

  return (
    <div className="min-h-screen bg-[#040d08] text-white flex flex-col"
         style={{ transition: 'opacity 0.4s ease, transform 0.4s ease',
                  opacity: visible ? 1 : 0,
                  transform: visible ? 'translateY(0)' : 'translateY(12px)' }}>

      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-white/5 flex-shrink-0">
        <button onClick={() => router.push('/')}
                className="flex items-center gap-2 text-white/60 hover:text-white transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-teal-500/15 border border-teal-500/25 flex items-center justify-center">
              <svg className="w-3 h-3 text-teal-400" viewBox="0 0 24 24" fill="currentColor">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <span className="font-mono text-sm font-semibold text-white/80">CodeCritic</span>
          </div>
        </button>

        <div className="flex items-center gap-3">
          <ScoreBadge score={result.pass_score} />
          <span className="text-xs text-white/60 font-mono">{board}</span>
        </div>
      </nav>

      {/* Prompt banner */}
      <div className="px-6 py-3 border-b border-zinc-900/60 bg-zinc-950/50">
        <p className="text-xs text-white/60 font-mono truncate">
          <span className="text-white/50 mr-2">prompt:</span>{prompt}
        </p>
      </div>

      {/* Main content */}
      <div className="flex-1 p-6 flex flex-col gap-5 overflow-auto">

        {/* Top row — Code + Circuit side by side */}
        <div className="grid grid-cols-2 gap-5" style={{ minHeight: '420px' }}>

          {/* Code */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-900 flex-shrink-0">
              <div className="flex items-center gap-3">
                <div className="flex gap-1">
                  <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                  <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                  <div className="w-2.5 h-2.5 rounded-full bg-zinc-800" />
                </div>
                <span className="text-xs font-mono text-white/70">sketch.ino</span>
              </div>
              <div className="flex items-center gap-1.5">
                <button onClick={handleCopy}
                        className="text-xs font-mono text-white/60 hover:text-white
                                   px-2.5 py-1 rounded border border-zinc-800 hover:border-zinc-700
                                   transition-colors">
                  {copied ? '✓ copied' : '⎘ copy'}
                </button>
                <button onClick={() => downloadSketch(result.session_id)}
                        className="text-xs font-mono text-white/60 hover:text-white
                                   px-2.5 py-1 rounded border border-zinc-800 hover:border-zinc-700
                                   transition-colors">
                  ↓ .ino
                </button>
              </div>
            </div>
            <pre className="flex-1 p-5 text-xs font-mono text-white/90 overflow-auto leading-relaxed">
              <code>{result.sketch_ino}</code>
            </pre>
          </div>

          {/* Circuit */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-900 flex-shrink-0">
              <span className="text-xs font-mono text-white/70">circuit diagram</span>
              <button onClick={() => circuitRef.current?.downloadSVG()}
                      disabled={!result.diag_json}
                      className="text-xs font-mono text-white/60 hover:text-white
                                 px-2.5 py-1 rounded border border-zinc-800 hover:border-zinc-700
                                 transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
                ↓ .svg
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              {result.diag_json
                ? <CircuitViewer ref={circuitRef} diag_json={result.diag_json} />
                : (
                  <div className="h-full flex flex-col items-center justify-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800
                                    flex items-center justify-center">
                      <svg className="w-5 h-5 text-white/50" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                      </svg>
                    </div>
                    <p className="text-xs text-white/60 font-mono">no circuit generated</p>
                  </div>
                )}
            </div>
          </div>
        </div>

        {/* Bottom row — BOM + Verification + Export */}
        <div className="grid grid-cols-[1fr,280px,200px] gap-5">

          {/* BOM */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-900">
              <span className="text-xs font-mono text-white/70">bill of materials</span>
            </div>
            {bom.length > 0 ? (
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-900">
                    {['Component', 'Qty', 'Specs'].map(h => (
                      <th key={h} className="text-left px-4 py-2.5 text-[10px] font-mono
                                             text-white/60 uppercase tracking-widest">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {bom.map((row, i) => (
                    <tr key={i} className="border-b border-zinc-900/60 last:border-0 hover:bg-zinc-900/30">
                      <td className="px-4 py-2.5 text-xs font-mono text-white/90">{row.component}</td>
                      <td className="px-4 py-2.5 text-xs font-mono text-white/60">{row.qty}</td>
                      <td className="px-4 py-2.5 text-xs font-mono text-teal-400">{row.specs || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="px-4 py-6 text-xs text-white/50 font-mono">no components parsed</p>
            )}
          </div>

          {/* Verification */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-900">
              <span className="text-xs font-mono text-white/70">verification</span>
            </div>
            <div className="px-4 py-3">
              <div className="flex items-center justify-between mb-4">
                <ScoreBadge score={result.pass_score} />
                <span className="text-xs font-mono text-white/60">
                  {Math.round(result.pass_score * 100)}%
                </span>
              </div>
              {checks.map(c => <CheckRow key={c.label} {...c} />)}
            </div>
          </div>

          {/* Export */}
          <div className="bg-zinc-950 border border-zinc-900 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-zinc-900">
              <span className="text-xs font-mono text-white/70">export</span>
            </div>
            <div className="p-4 flex flex-col gap-2">
              <button onClick={() => downloadSketch(result.session_id)}
                      className="w-full py-2.5 rounded-lg border border-zinc-800 hover:border-zinc-700
                                 text-xs font-mono text-white/80 hover:text-white
                                 transition-colors flex items-center justify-center gap-2">
                ↓ sketch.ino
              </button>
              <button onClick={() => circuitRef.current?.downloadSVG()}
                      disabled={!result.diag_json}
                      className="w-full py-2.5 rounded-lg border border-zinc-800 hover:border-zinc-700
                                 text-xs font-mono text-white/80 hover:text-white
                                 transition-colors flex items-center justify-center gap-2
                                 disabled:opacity-30 disabled:cursor-not-allowed">
                ↓ diagram.svg
              </button>
              <button
                onClick={() => { downloadSketch(result.session_id); circuitRef.current?.downloadSVG() }}
                className="w-full py-2.5 rounded-lg bg-teal-500 hover:bg-teal-400
                           text-xs font-mono font-semibold text-zinc-950
                           transition-colors flex items-center justify-center gap-2 mt-1">
                ↓ export all
              </button>
              <button onClick={() => router.push('/')}
                      className="w-full py-2.5 rounded-lg border border-zinc-800 hover:border-teal-800
                                 text-xs font-mono text-white/60 hover:text-teal-400
                                 transition-colors flex items-center justify-center gap-2 mt-1">
                + new project
              </button>
              {/* Deploy */}
              <div className="border-t border-zinc-800/60 mt-2 pt-3">
                <DeployButton sessionId={result.session_id} board={board} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}