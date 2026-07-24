import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import NodusLogo from './NodusLogo'

/** Spoločný obal pre právne stránky (podmienky, ochrana údajov). */
export default function LegalShell({
  title, updated, children,
}: { title: string; updated: string; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-bg dark:bg-bg-dark text-gray-900 dark:text-gray-100">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-3xl mx-auto px-5 h-16 flex items-center justify-between">
          <Link to="/"><NodusLogo variant="wordmark" size={26} /></Link>
          <Link to="/" className="btn-ghost text-sm">← Späť</Link>
        </div>
      </header>
      <main className="max-w-3xl mx-auto px-5 py-10">
        <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
          ⚠️ <strong>Koncept dokumentu.</strong> Toto je vzorové znenie. Pred ostrým
          spustením ho daj skontrolovať právnikovi a doplň údaje o prevádzkovateľovi
          (miesta označené <code>[…]</code>).
        </div>
        <h1 className="text-3xl font-bold mb-1">{title}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">Účinné od: {updated}</p>
        <div className="space-y-4 text-gray-700 dark:text-gray-300 leading-relaxed">
          {children}
        </div>
      </main>
    </div>
  )
}

export function H2({ children }: { children: ReactNode }) {
  return <h2 className="text-xl font-semibold text-gray-900 dark:text-white pt-5">{children}</h2>
}

export function P({ children }: { children: ReactNode }) {
  return <p>{children}</p>
}

export function UL({ items }: { items: ReactNode[] }) {
  return (
    <ul className="list-disc pl-6 space-y-1">
      {items.map((it, i) => <li key={i}>{it}</li>)}
    </ul>
  )
}
