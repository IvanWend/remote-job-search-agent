import { Icon } from './Icon'
import type { Lang } from '../lib/i18n'

export function LanguageToggle({
  lang,
  onChange,
}: {
  lang: Lang
  onChange: (lang: Lang) => void
}) {
  return (
    <div
      className="flex border border-[var(--border)] bg-[var(--panel)] p-0.5"
      role="group"
      aria-label="Language"
    >
      {(['en', 'ru'] as const).map((option) => (
        <button
          key={option}
          type="button"
          aria-pressed={lang === option}
          onClick={() => onChange(option)}
          className={`h-5 px-2 font-mono text-[9px] font-semibold transition ${
            lang === option
              ? 'bg-cyan-300 text-[var(--accent-contrast)]'
              : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
          }`}
        >
          {option.toUpperCase()}
        </button>
      ))}
    </div>
  )
}

export function ThemeToggle({
  theme,
  onToggle,
}: {
  theme: 'dark' | 'light'
  onToggle: () => void
}) {
  const next = theme === 'dark' ? 'light' : 'dark'
  return (
    <button
      type="button"
      aria-label={`Switch to ${next} theme`}
      onClick={onToggle}
      className="flex h-7 w-7 items-center justify-center border border-[var(--border)] text-[var(--text-tertiary)] hover:border-cyan-400/40 hover:text-cyan-500"
    >
      <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={14} />
    </button>
  )
}
