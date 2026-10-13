import { Icon } from './Icon'
import { ui, type Lang } from '../lib/i18n'

// Placeholder until the report generation job exists (PLAN week 6). Renders the
// Figma "empty" state — the real report payload is not on the wire yet.
export function MonthlyReport({ lang }: { lang: Lang }) {
  const t = ui[lang]
  return (
    <section className="h-full overflow-y-auto">
      <div className="mx-auto max-w-[1180px] px-4 py-7 sm:px-8 sm:py-10">
        <div className="mb-8 border-b border-[var(--border)] pb-5">
          <p className="mb-1.5 font-mono text-[9px] tracking-[0.12em] text-[var(--accent-text)]">
            {t.intelligence}
          </p>
          <h1 className="text-[26px] font-medium tracking-[-0.035em] text-[var(--text-primary)]">
            {t.reportTitle}
          </h1>
        </div>
        <div className="flex min-h-[440px] items-center justify-center border border-[var(--border)] bg-[var(--panel)] text-center">
          <div className="max-w-sm px-6">
            <div className="mx-auto mb-5 flex h-10 w-10 items-center justify-center border border-[var(--border)] text-cyan-500">
              <Icon name="bolt" size={17} />
            </div>
            <h2 className="text-[17px] font-semibold text-[var(--text-primary)]">
              {t.generatedMonthly}
            </h2>
            <p className="mt-2 text-[12px] leading-5 text-[var(--text-secondary)]">
              {t.emptyText}
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
