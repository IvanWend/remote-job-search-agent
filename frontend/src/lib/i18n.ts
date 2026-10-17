// UI chrome strings, both locales. The agent's *prose* (headline, key_finding,
// quote text, table titles) is still English-only (backend localisation is a
// later milestone); this covers the chrome so the RU/EN toggle is visible and
// wired end-to-end.

export type Lang = 'en' | 'ru'

type Messages = {
  intelligence: string
  analysis: string
  monthly: string
  ask: string
  defaultQuery: string
  run: string
  cancel: string
  complete: string
  thinking: string
  emptyTitle: string
  emptyHint: string
  suggestions: string
  errorTitle: string
  errorHint: string
  reportTitle: string
  generatedMonthly: string
  emptyText: string
  // Contract render chrome.
  keyFinding: string
  evidence: string
  salaryNotStated: string
  perMonth: string
  more: (n: number) => string
}

const en: Messages = {
  intelligence: 'TECH MARKET INTELLIGENCE',
  analysis: 'Analysis',
  monthly: 'Monthly report',
  ask: 'Ask the corpus…',
  defaultQuery: 'What skills command the highest salaries for remote backend roles?',
  run: 'Run query',
  cancel: 'Stop',
  complete: 'ANALYSIS · COMPLETE',
  thinking: 'Thinking…',
  emptyTitle: 'Ask about the job market',
  emptyHint:
    'Questions are answered by an agent over real job postings from four boards.',
  suggestions: 'SUGGESTED',
  errorTitle: 'Something went wrong',
  errorHint: 'The query could not be completed. Try again.',
  reportTitle: 'Monthly Report',
  generatedMonthly: 'Reports are generated monthly',
  emptyText:
    'The first report will appear here when a complete month of market data is available.',
  keyFinding: 'KEY FINDING',
  evidence: 'Evidence',
  salaryNotStated: 'Salary not stated',
  perMonth: '/mo',
  more: (n) => `+${n} more`,
}

const ru: Messages = {
  intelligence: 'АНАЛИТИКА ТЕХ-РЫНКА',
  analysis: 'Аналитика',
  monthly: 'Ежемесячный отчёт',
  ask: 'Задать вопрос по базе…',
  defaultQuery: 'Какие навыки дают самые высокие зарплаты в удалённых backend-вакансиях?',
  run: 'Запустить',
  cancel: 'Стоп',
  complete: 'АНАЛИЗ · ГОТОВО',
  thinking: 'Анализируем…',
  emptyTitle: 'Спросите о рынке труда',
  emptyHint: 'Агент отвечает на вопросы по реальным вакансиям из четырёх источников.',
  suggestions: 'ПРЕДЛОЖЕННЫЕ',
  errorTitle: 'Что-то пошло не так',
  errorHint: 'Не удалось выполнить запрос. Попробуйте ещё раз.',
  reportTitle: 'Ежемесячный отчёт',
  generatedMonthly: 'Отчёты формируются раз в месяц',
  emptyText:
    'Первый отчёт появится здесь, когда будет доступен полный месяц рыночных данных.',
  keyFinding: 'КЛЮЧЕВОЙ ВЫВОД',
  evidence: 'Подтверждения',
  salaryNotStated: 'Зарплата не указана',
  perMonth: '/мес',
  more: (n) => `+${n} ещё`,
}

export const ui: Record<Lang, Messages> = { en, ru }

export const questions: Record<Lang, { group: string; items: string[] }[]> = {
  en: [
    { group: 'SKILLS', items: ['Which backend skills appear most?', 'Fastest-growing skill pairs', 'Rust roles by geography'] },
    { group: 'SALARIES', items: ['Highest-paid remote roles', 'Median salary by seniority', 'Compare USD and EUR salaries'] },
    { group: 'ROLES', items: ['Remote staff-level openings', 'Engineering roles in Europe', 'Companies hiring for platform'] },
  ],
  ru: [
    { group: 'НАВЫКИ', items: ['Какие backend-навыки встречаются чаще?', 'Самые быстрорастущие пары навыков', 'География вакансий с Rust'] },
    { group: 'ЗАРПЛАТЫ', items: ['Самые высокооплачиваемые удалённые роли', 'Медиана зарплаты по уровню', 'Сравнить зарплаты в USD и EUR'] },
    { group: 'РОЛИ', items: ['Удалённые вакансии уровня staff', 'Инженерные роли в Европе', 'Компании, нанимающие platform-инженеров'] },
  ],
}
