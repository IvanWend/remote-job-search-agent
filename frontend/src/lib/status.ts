// What the user sees while a tool runs. Tool names never cross the UI.
const STATUS: Record<string, string> = {
  vector_search: 'Searching postings…',
  sql_query: 'Crunching the numbers…',
  role_detail: 'Reading a posting…',
}

export function statusFor(toolName: string): string {
  return STATUS[toolName] ?? 'Working…'
}
