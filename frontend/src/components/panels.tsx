import type { ReactNode } from 'react'
import { ui, type Lang } from '../lib/i18n'
import type { ToolStep, VectorHit } from '../lib/types'

// Display caps: the panels are a summary, not a data dump.
const MAX_SKILLS = 10
const MAX_ROLES = 5

// --- formatters -------------------------------------------------------------

const CURRENCY_SYMBOL: Record<string, string> = {
  USD: '$',
  EUR: '€',
  RUB: '₽',
  GBP: '£',
  CAD: 'C$',
  AUD: 'A$',
}

function fmtInt(n: number | null | undefined, lang: Lang): string | null {
  if (n === null || n === undefined) return null
  return new Intl.NumberFormat(lang === 'ru' ? 'ru-RU' : 'en-US').format(n)
}

function currencySymbol(code: string | null | undefined): string {
  if (!code) return ''
  return CURRENCY_SYMBOL[code] ?? `${code} `
}

type SalaryFields = {
  salary_min?: number | null
  salary_max?: number | null
  salary_currency?: string | null
}

// The boards store absent enums as the string "unknown", not null, so truthiness
// alone would render "UNKNOWN" badges.
function isBlank(value: string | null | undefined): boolean {
  return !value || value.trim() === '' || value.toLowerCase() === 'unknown'
}

// A hit with neither skills nor a salary renders as an empty shell; keep only
// hits that carry something to show.
function hasSubstance(hit: VectorHit): boolean {
  const hasStack = Array.isArray(hit.stack) && hit.stack.length > 0
  const hasSalary = hit.salary_min != null || hit.salary_max != null
  return hasStack || hasSalary
}

// One panel for all vector_search calls in a run: merge the steps, dedupe by
// the stable key, and drop substance-less hits.
function mergeVectorHits(steps: ToolStep[]): VectorHit[] {
  const seen = new Set<string>()
  const out: VectorHit[] = []
  for (const step of steps) {
    if (step.name !== 'vector_search' || !Array.isArray(step.content)) continue
    for (const hit of step.content as VectorHit[]) {
      const key = `${hit.raw_posting_id ?? '?'}:${hit.role_index ?? '?'}`
      if (seen.has(key)) continue
      seen.add(key)
      if (hasSubstance(hit)) out.push(hit)
    }
  }
  return out
}

// role_detail records (full row minus description) share the display fields
// with vector hits, so they render through the same cards.
function mergeRoleDetails(steps: ToolStep[]): VectorHit[] {
  const seen = new Set<string>()
  const out: VectorHit[] = []
  for (const step of steps) {
    if (step.name !== 'role_detail') continue
    const record = step.content as VectorHit | null
    if (!record || typeof record !== 'object') continue
    const key = `${record.raw_posting_id ?? '?'}:${record.role_index ?? '?'}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push(record)
  }
  return out
}

function salaryLine(fields: SalaryFields, lang: Lang, monthly: string): string | null {
  const sym = currencySymbol(fields.salary_currency)
  const lo = fmtInt(fields.salary_min, lang)
  const hi = fmtInt(fields.salary_max, lang)
  if (lo !== null && hi !== null && lo !== hi) return `${sym}${lo}–${hi} ${monthly}`
  if (hi !== null) return `${sym}${hi} ${monthly}`
  if (lo !== null) return `${sym}${lo}+ ${monthly}`
  return null
}

// --- primitives -------------------------------------------------------------

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border border-[var(--border)] bg-[var(--panel)]">
      <div className="border-b border-[var(--border)] px-4 py-3">
        <p className="text-[12px] font-semibold text-[var(--text-primary)]">{title}</p>
      </div>
      {children}
    </section>
  )
}

function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="rounded-[3px] border border-[var(--border)] px-1.5 py-0.5 font-mono text-[9px] tracking-[0.04em] text-[var(--text-tertiary)]">
      {children}
    </span>
  )
}

function DataTable({ headers, rows }: { headers: string[]; rows: (string | number)[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-[var(--border)]">
            {headers.map((header, index) => (
              <th
                key={header}
                className={`px-3 py-2 font-mono text-[9px] font-medium uppercase tracking-[0.08em] text-[var(--text-faint)] ${
                  index ? 'text-right' : ''
                }`}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-[var(--border-soft)] last:border-0">
              {row.map((cell, cellIndex) => (
                <td
                  key={cellIndex}
                  className={`whitespace-nowrap px-3 py-2.5 font-mono text-[10px] ${
                    cellIndex ? 'text-right text-[var(--text-secondary)]' : 'text-[var(--text-primary)]'
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// --- panel renderers --------------------------------------------------------

function SkillBars({ rows, lang }: { rows: { skill: string; roles: number }[]; lang: Lang }) {
  const max = Math.max(1, ...rows.map((r) => r.roles))
  return (
    <div className="space-y-3 p-4">
      {rows.map((row, index) => (
        <div key={row.skill} className="grid grid-cols-[20px_90px_1fr_44px] items-center gap-2">
          <span className="font-mono text-[9px] text-[var(--text-faint)]">
            {String(index + 1).padStart(2, '0')}
          </span>
          <span className="truncate text-[11px] text-[var(--text-secondary)]">{row.skill}</span>
          <div className="h-1.5 overflow-hidden bg-[var(--fill-soft)]">
            <div
              className="h-full bg-cyan-400/80"
              style={{ width: `${Math.round((row.roles / max) * 100)}%` }}
            />
          </div>
          <span className="text-right font-mono text-[10px] text-[var(--text-tertiary)]">
            {fmtInt(row.roles, lang)}
          </span>
        </div>
      ))}
    </div>
  )
}

function RoleCards({ hits, lang }: { hits: VectorHit[]; lang: Lang }) {
  const t = ui[lang]
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {hits.map((hit, index) => {
        const salary = salaryLine(hit, lang, t.perMonth)
        const seniority = isBlank(hit.seniority) ? null : hit.seniority
        const policy = isBlank(hit.remote_policy) ? null : hit.remote_policy
        const location = isBlank(hit.location) ? null : hit.location
        const hasStack = Array.isArray(hit.stack) && hit.stack.length > 0
        return (
          <article
            key={`${hit.raw_posting_id ?? index}-${hit.role_index ?? index}`}
            className="border border-[var(--border)] bg-[var(--surface-raised)]"
          >
            <div className={`p-3 ${salary !== null || hasStack ? 'border-b border-[var(--border-soft)]' : ''}`}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate text-[12px] font-semibold text-[var(--text-primary)]">
                    {hit.company ?? '—'}
                  </p>
                  <p className="mt-0.5 truncate text-[11px] text-[var(--text-secondary)]">
                    {hit.title ?? ''}
                  </p>
                </div>
                {hit.source && (
                  <span className="shrink-0 rounded-[3px] border border-[var(--border)] px-1.5 py-0.5 font-mono text-[9px] text-[var(--text-tertiary)]">
                    {hit.source}
                  </span>
                )}
              </div>
              {(seniority || policy || location) && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {seniority && <Badge>{seniority.toUpperCase()}</Badge>}
                  {policy && <Badge>{policy.toUpperCase()}</Badge>}
                  {location && <Badge>{location}</Badge>}
                </div>
              )}
            </div>
            {(salary !== null || hasStack) && (
              <div className="space-y-2.5 p-3">
                {salary && (
                  <p className="font-mono text-[13px] font-medium text-[var(--text-primary)]">
                    {salary}
                  </p>
                )}
                {hasStack && (
                  <div className="flex flex-wrap gap-1.5">
                    {hit.stack!.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-[3px] bg-[var(--fill-soft)] px-2 py-1 font-mono text-[10px] text-[var(--text-secondary)]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </article>
        )
      })}
    </div>
  )
}

// --- the panel list ---------------------------------------------------------

export function ToolPanels({ steps, lang }: { steps: ToolStep[]; lang: Lang }) {
  const t = ui[lang]
  // A run that fetched a specific role (role_detail) is a "tell me about this
  // position" question: the vector_search in it only located the key, so its
  // hit list is noise — show the fetched role instead.
  const roleDetails = mergeRoleDetails(steps)
  const rolePanelAt = steps.findIndex(
    (step) => step.name === 'role_detail' && step.content !== null && step.content !== undefined,
  )
  const vectorHits = roleDetails.length > 0 ? [] : mergeVectorHits(steps)
  const vectorPanelAt = steps.findIndex((step) => step.name === 'vector_search')
  return (
    <div className="mt-8 space-y-6">
      {steps.map((step, index) => {
        if (step.content === null || step.content === undefined) return null

        if (step.name === 'vector_search') {
          if (index !== vectorPanelAt || vectorHits.length === 0) return null
          return (
            <Panel key={index} title={t.matchingRoles}>
              <div className="p-3">
                <RoleCards hits={vectorHits.slice(0, MAX_ROLES)} lang={lang} />
              </div>
            </Panel>
          )
        }

        if (step.name === 'role_detail') {
          if (index !== rolePanelAt || roleDetails.length === 0) return null
          return (
            <Panel key={index} title={t.roleDetail}>
              <div className="p-3">
                <RoleCards hits={roleDetails.slice(0, MAX_ROLES)} lang={lang} />
              </div>
            </Panel>
          )
        }

        if (step.name === 'sql_query') {
          const rows = step.content as Record<string, unknown>[]
          if (!Array.isArray(rows) || rows.length === 0) return null
          const query = step.args.query

          if (query === 'skill_frequency') {
            const bars = rows as unknown as { skill: string; roles: number }[]
            return (
              <Panel key={index} title={t.skills}>
                <SkillBars rows={bars.slice(0, MAX_SKILLS)} lang={lang} />
              </Panel>
            )
          }

          if (query === 'salary_by_seniority') {
            const data = rows as unknown as {
              seniority: string
              roles: number
              median_max_monthly: number | null
            }[]
            return (
              <Panel key={index} title={`${t.salaryBySeniority} · ${String(step.args.currency ?? 'USD')}`}>
                <DataTable
                  headers={[t.seniority, t.roles, t.median]}
                  rows={data.map((r) => [r.seniority, r.roles, fmtInt(r.median_max_monthly, lang) ?? '—'])}
                />
              </Panel>
            )
          }

          if (query === 'salary_by_currency') {
            const data = rows as unknown as {
              currency: string | null
              n: number
              median_max_monthly: number | null
            }[]
            return (
              <Panel key={index} title={t.salaryByCurrency}>
                <DataTable
                  headers={[t.currency, t.roles, t.median]}
                  rows={data.map((r) => [r.currency ?? '—', r.n, fmtInt(r.median_max_monthly, lang) ?? '—'])}
                />
              </Panel>
            )
          }

          if (query === 'top_salaries') {
            const data = rows as unknown as {
              company: string | null
              title: string | null
              salary_min: number | null
              salary_max: number | null
              salary_currency: string | null
            }[]
            return (
              <Panel key={index} title={`${t.topSalaries} · ${String(step.args.currency ?? 'USD')}`}>
                <DataTable
                  headers={[t.company, t.title, t.salary]}
                  rows={data.map((r) => [
                    r.company ?? '—',
                    r.title ?? '—',
                    salaryLine(r, lang, t.perMonth) ?? '—',
                  ])}
                />
              </Panel>
            )
          }
        }

        return null
      })}
    </div>
  )
}
