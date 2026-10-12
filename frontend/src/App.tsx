import { useEffect, useRef, useState } from 'react'
import { streamAnswer } from './lib/sse'
import type { StreamEvent } from './lib/sse'
import { statusFor } from './lib/status'
import { TurnView } from './components/Turn'
import type { Turn } from './components/Turn'

const EXAMPLES = [
  'Which companies are hiring senior remote engineers?',
  'What are the most in-demand skills right now?',
  'How do React salaries compare to Python salaries?',
]

function App() {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [streaming, setStreaming] = useState(false)
  const controllerRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  // Keep the newest exchange in view as the status line flips and answers land.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turns])

  // Every event from sse.ts patches the turn currently in flight — always the
  // last one. React state setters are stable, so this closure never goes stale
  // even though it's recreated each render.
  function updateLast(patch: Partial<Turn>) {
    setTurns((prev) => {
      if (prev.length === 0) return prev
      const copy = [...prev]
      copy[copy.length - 1] = { ...copy[copy.length - 1], ...patch }
      return copy
    })
  }

  function handleEvent(e: StreamEvent) {
    switch (e.event) {
      case 'tool_call':
        updateLast({ status: statusFor(e.data.name) })
        break
      case 'tool_result':
        break // tool output is hidden; the frame only signals progress
      case 'answer':
        updateLast({ answer: e.data.answer, status: null })
        setStreaming(false)
        break
      case 'error':
        updateLast({ error: e.data.message, status: null })
        setStreaming(false)
        break
    }
  }

  // Fired from the submit handler or an example chip, NOT an effect: that keeps
  // it single-shot even under React StrictMode's dev double-invoke of effects.
  function start(q: string) {
    const text = q.trim()
    if (!text || streaming) return

    setTurns((prev) => [
      ...prev,
      { question: text, status: 'Thinking…', answer: null, error: null },
    ])
    setQuestion('')
    setStreaming(true)

    const controller = new AbortController()
    controllerRef.current = controller

    streamAnswer(text, handleEvent, controller.signal).catch((err) => {
      if (controller.signal.aborted) return // cancel is a stop, not an error
      updateLast({
        error: err instanceof Error ? err.message : String(err),
        status: null,
      })
      setStreaming(false)
    })
  }

  function cancel() {
    controllerRef.current?.abort()
    controllerRef.current = null
    updateLast({ status: null })
    setStreaming(false)
  }

  return (
    <main className="flex h-screen flex-col bg-white text-neutral-900">
      <header className="shrink-0 border-b border-neutral-200 px-4 py-3">
        <h1 className="text-sm font-medium">Remote job search agent</h1>
      </header>

      <div className="flex-1 overflow-y-auto">
        {turns.length === 0 ? (
          <div className="mx-auto flex h-full max-w-3xl flex-col items-center justify-center gap-8 px-4 text-center">
            <div>
              <h2 className="text-2xl font-semibold">Ask about the job market</h2>
              <p className="mt-2 text-neutral-500">
                Job-related questions, answered by an intelligent agent over real
                job postings.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {EXAMPLES.map((q) => (
                <button
                  key={q}
                  className="rounded-full border border-neutral-200 px-4 py-2 text-sm text-neutral-600 hover:bg-neutral-50"
                  onClick={() => start(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-8 px-4 py-6">
            {turns.map((turn, i) => (
              <TurnView key={i} turn={turn} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="mx-auto w-full max-w-3xl shrink-0 px-4 pb-4">
        <form
          className="flex items-end gap-2 rounded-2xl border border-neutral-300 bg-white p-2 shadow-sm focus-within:border-neutral-400"
          onSubmit={(e) => {
            e.preventDefault()
            start(question)
          }}
        >
          <textarea
            rows={1}
            className="max-h-40 flex-1 resize-none bg-transparent px-3 py-2 text-[15px] outline-none"
            placeholder="Ask about the job corpus…"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                start(question)
              }
            }}
          />
          {streaming ? (
            <button
              type="button"
              aria-label="Stop"
              className="rounded-full bg-neutral-900 p-2 text-white"
              onClick={cancel}
            >
              <svg viewBox="0 0 16 16" className="h-4 w-4" fill="currentColor">
                <rect x="3" y="3" width="10" height="10" rx="1.5" />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              aria-label="Send"
              disabled={!question.trim()}
              className="rounded-full bg-neutral-900 p-2 text-white disabled:opacity-30"
            >
              <svg viewBox="0 0 16 16" className="h-4 w-4" fill="currentColor">
                <path d="M8 12.5a.75.75 0 0 1-.75-.75V5.56L4.53 8.28a.75.75 0 0 1-1.06-1.06l4-4a.75.75 0 0 1 1.06 0l4 4a.75.75 0 0 1-1.06 1.06L8.75 5.56v6.19A.75.75 0 0 1 8 12.5Z" />
              </svg>
            </button>
          )}
        </form>
      </div>
    </main>
  )
}

export default App
