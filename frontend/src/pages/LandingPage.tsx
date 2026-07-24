import { Link } from 'react-router-dom'
import {
  GitBranch, TrendingUp, BarChart3, Users, Sparkles, ShieldCheck, Check, ArrowRight,
} from 'lucide-react'
import NodusLogo from '../components/NodusLogo'
import { useDarkMode } from '../hooks/useDarkMode'
import { Sun, Moon } from 'lucide-react'

const FEATURES = [
  { icon: GitBranch, title: 'Kritická cesta (CPM)', text: 'Automaticky nájde najdlhšiu sekvenciu úloh — vieš presne, čo posúva celý projekt. ES/EF/LS/LF a rezervy pri každej úlohe.' },
  { icon: TrendingUp, title: 'PERT pravdepodobnosť', text: 'Trojbodový odhad a pravdepodobnosť, že stihneš termín. Žiadne hádanie — čísla podložené štatistikou.' },
  { icon: BarChart3, title: 'Gantt & sieťový diagram', text: 'Interaktívna vizualizácia harmonogramu aj závislostí. Rezerva a kritické úlohy na prvý pohľad.' },
  { icon: Users, title: 'Tím & zdroje', text: 'Prideľuj úlohy, sleduj vyťaženie a odhaľ preťaženie (over-allocation) skôr, než sa stane problémom.' },
  { icon: Sparkles, title: 'AI generátor úloh', text: 'Popíš projekt vlastnými slovami — AI vytvorí úlohy, trvania a závislosti, ktoré rovno padnú do CPM.' },
  { icon: ShieldCheck, title: 'Bezpečné a multi-tenant', text: 'Izolované organizácie, šifrované heslá, kontrola prístupu. Tvoje dáta vidíš len ty a tvoj tím.' },
]

const PLANS = [
  {
    name: 'Free', price: '€0', period: 'navždy', highlight: false,
    features: ['2 projekty', 'do 5 členov tímu', 'CPM, Gantt, sieťový diagram', 'Základná správa tímu'],
    cta: 'Začať zadarmo',
  },
  {
    name: 'Starter', price: '€7', period: '/ používateľ / mesiac', highlight: true,
    features: ['Neobmedzené projekty', 'do 15 členov', 'PDF export & CSV', 'Notifikácie termínov', 'Prioritná podpora'],
    cta: 'Vyskúšať Starter',
  },
  {
    name: 'Team', price: '€12', period: '/ používateľ / mesiac', highlight: false,
    features: ['Všetko zo Starter', 'Neobmedzený tím', 'Real-time spolupráca', 'AI asistent', 'Pokročilý CPM reporting'],
    cta: 'Vyskúšať Team',
  },
]

export default function LandingPage() {
  const { dark, toggle } = useDarkMode()

  return (
    <div className="min-h-screen bg-bg dark:bg-bg-dark text-gray-900 dark:text-gray-100">
      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 backdrop-blur bg-bg/80 dark:bg-bg-dark/80 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          <NodusLogo variant="wordmark" size={28} />
          <div className="flex items-center gap-2">
            <button onClick={toggle} className="btn-ghost p-2" aria-label="Prepnúť tému">
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <Link to="/login" className="btn-ghost text-sm hidden sm:inline-flex">Prihlásiť sa</Link>
            <Link to="/signup" className="btn-primary text-sm">Vytvoriť účet</Link>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[42rem] h-[42rem] bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative max-w-3xl mx-auto px-5 pt-20 pb-16 text-center">
          <span className="badge bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 mb-6">
            Projektový manažment na kritickej ceste
          </span>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-tight">
            Vieš, ktoré úlohy naozaj{' '}
            <span className="text-brand-500">rozhodujú</span> o termíne?
          </h1>
          <p className="mt-6 text-lg text-gray-600 dark:text-gray-400">
            Nodus počíta kritickú cestu (CPM) a pravdepodobnosť termínu (PERT) — nie len farebné pruhy.
            Matematicky podložené plánovanie, ktoré drahé nástroje účtujú a lacné nemajú.
          </p>
          <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to="/signup" className="btn-primary text-base px-6 py-3 flex items-center gap-2">
              Vyskúšať zadarmo <ArrowRight size={18} />
            </Link>
            <Link to="/login" className="btn-ghost text-base px-6 py-3">Už mám účet</Link>
          </div>
          <p className="mt-4 text-xs text-gray-400">Bez platobnej karty · Free plán navždy</p>
        </div>
      </section>

      {/* ── Odlišovač ───────────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-5 py-8">
        <div className="card p-6 sm:p-8 text-center">
          <p className="text-sm uppercase tracking-wide text-gray-400 mb-2">Prečo Nodus</p>
          <p className="text-lg sm:text-xl text-gray-700 dark:text-gray-300">
            Trello, Asana či Monday ti ukážu <strong>Ganttov graf</strong>. To je vizualizácia, nie analýza.
            Nodus navyše <strong className="text-brand-500">vypočíta kritickú cestu a rezervy</strong> —
            takže vieš, kde tlačiť a kde máš priestor.
          </p>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-5 py-14">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-3">Všetko pre riadenie projektu</h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-10">Od plánovania po dokončenie — s matematickým jadrom.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card p-6">
              <div className="w-11 h-11 rounded-lg bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center mb-4">
                <Icon className="text-brand-500" size={22} />
              </div>
              <h3 className="font-semibold text-lg mb-1.5">{title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Cenník ──────────────────────────────────────────────────────── */}
      <section id="cennik" className="max-w-6xl mx-auto px-5 py-14">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-3">Jednoduchý cenník</h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-10">Začni zadarmo, plať až keď rastieš.</p>
        <div className="grid md:grid-cols-3 gap-6 items-start">
          {PLANS.map((p) => (
            <div key={p.name} className={`card p-7 relative ${p.highlight ? 'ring-2 ring-brand-500 md:-translate-y-2' : ''}`}>
              {p.highlight && (
                <span className="badge bg-brand-500 text-white absolute -top-3 left-1/2 -translate-x-1/2">Najobľúbenejší</span>
              )}
              <h3 className="font-semibold text-lg">{p.name}</h3>
              <div className="mt-3 mb-1 flex items-baseline gap-1">
                <span className="text-4xl font-bold">{p.price}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">{p.period}</span>
              </div>
              <ul className="mt-6 space-y-3">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="text-brand-500 shrink-0 mt-0.5" size={16} />
                    <span className="text-gray-700 dark:text-gray-300">{f}</span>
                  </li>
                ))}
              </ul>
              <Link
                to="/signup"
                className={`mt-7 w-full justify-center inline-flex ${p.highlight ? 'btn-primary' : 'btn-ghost border border-gray-200 dark:border-gray-700'}`}
              >
                {p.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-5 py-16">
        <div className="card p-10 text-center bg-gradient-to-br from-brand-500 to-brand-700 border-0">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Rozbehni svoj prvý projekt za 2 minúty</h2>
          <p className="mt-3 text-white/80">Vytvor si organizáciu, pozvi tím a nechaj Nodus počítať.</p>
          <Link to="/signup" className="mt-7 inline-flex items-center gap-2 bg-white text-brand-600 font-semibold px-6 py-3 rounded-lg hover:bg-gray-100 transition-colors">
            Vytvoriť účet zadarmo <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-5 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500 dark:text-gray-400">
          <NodusLogo variant="wordmark" size={22} />
          <p>© {new Date().getFullYear()} Nodus — projektový manažment na kritickej ceste</p>
          <div className="flex gap-4">
            <Link to="/login" className="hover:text-brand-500">Prihlásiť sa</Link>
            <Link to="/signup" className="hover:text-brand-500">Registrácia</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
