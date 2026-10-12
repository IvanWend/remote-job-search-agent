// One exchange in the chat: the user's question bubble, then the agent's side —
// a one-line status while it works, the markdown answer when it lands, or an
// error. Tool output is never rendered; a tool_call frame only advances the
// status line.

import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export type Turn = {
  question: string
  status: string | null
  answer: string | null
  error: string | null
}

function StatusLine({ text }: { text: string }) {
  return (
    <p className="flex items-center gap-2 text-sm text-neutral-500">
      <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neutral-400" />
      {text}
    </p>
  )
}

export function TurnView({ turn }: { turn: Turn }) {
  return (
    <div>
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl bg-neutral-100 px-4 py-2.5 text-[15px] whitespace-pre-wrap">
          {turn.question}
        </p>
      </div>
      <div className="mt-3">
        {turn.answer !== null ? (
          <div className="prose prose-neutral prose-sm max-w-none">
            <Markdown remarkPlugins={[remarkGfm]}>{turn.answer}</Markdown>
          </div>
        ) : turn.error !== null ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
            {turn.error}
          </p>
        ) : turn.status !== null ? (
          <StatusLine text={turn.status} />
        ) : null}
      </div>
    </div>
  )
}
