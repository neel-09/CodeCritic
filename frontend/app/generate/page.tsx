import { Suspense } from 'react'
import GenerateContent from './GenerateContent'

export default function GeneratePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-zinc-600 text-sm">Loading...</div>
      </div>
    }>
      <GenerateContent />
    </Suspense>
  )
}
