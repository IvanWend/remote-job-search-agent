// Wire shapes for the structured tool output the agent returns on the SSE
// stream. `content` stays `unknown` — panels narrow it per tool name.

export type ToolStep = {
  name: string
  args: Record<string, unknown>
  content: unknown
}

export type VectorHit = {
  raw_posting_id?: number
  role_index?: number
  title?: string | null
  company?: string | null
  location?: string | null
  seniority?: string | null
  remote_policy?: string | null
  stack?: string[]
  salary_min?: number | null
  salary_max?: number | null
  salary_currency?: string | null
  source?: string | null
  similarity?: number | null
}
