import { Link } from 'react-router-dom'
import {
  GitBranch, TrendingUp, BarChart3, Users, Sparkles, ShieldCheck,
  Check, ArrowRight, Sun, Moon, ListPlus, Network, Gauge, Minus,
} from 'lucide-react'
import NodusLogo from '../components/NodusLogo'
import CpmShowcase from '../components/CpmShowcase'
import { useDarkMode } from '../hooks/useDarkMode'

const STEPS = [
  {
    icon: ListPlus,
    title: 'Zapíš úlohy a trvania',
    text: 'Pri každej úlohe povieš, koľko dní zaberie. Ak si nie si istý, pridáš optimistický a pesimistický odhad.',
  },
  {
    icon: Network,
    title: 'Urči, čo na čom závisí',
    text: 'Maliari nemôžu pred elektrikármi. Tieto väzby sú jediné, čo musíš zadať navyše oproti bežnému zoznamu úloh.',
  },
  {
    icon: Gauge,
    title: 'Dostaneš termíny a rezervy',
    text: 'Nodus dopočíta najskoršie a najneskoršie možné začiatky, rezervy a kritickú cestu. Po každej zmene nanovo.',
  },
]

const FEATURES = [
  { icon: GitBranch, title: 'Kritická cesta (CPM)', text: 'Nájde najdlhšiu reťaz úloh a pri každej ukáže ES, EF, LS, LF aj časovú rezervu. Nie len farebný pruh.' },
  { icon: TrendingUp, title: 'PERT a pravdepodobnosť', text: 'Z trojbodového odhadu vypočíta očakávané trvanie a šancu, že termín stihneš. Namiesto jedného čísla, ktoré vyzerá presnejšie, než je.' },
  { icon: BarChart3, title: 'Gantt a sieťový diagram', text: 'Harmonogram aj sieť závislostí. Rezerva sa kreslí ako samostatný pruh, takže vidno, kde máš priestor.' },
  { icon: Users, title: 'Tím a vyťaženosť', text: 'Prideľuj úlohy a odhaľ preťaženie skôr, než sa z neho stane sklz.' },
  { icon: Sparkles, title: 'Generátor úloh', text: 'Popíš projekt vlastnými slovami a dostaneš úlohy, trvania aj závislosti, ktoré rovno vstúpia do výpočtu.' },
  { icon: ShieldCheck, title: 'Oddelené organizácie', text: 'Každá organizácia má vlastný priestor, heslá sú hashované cez bcrypt a prístup sa kontroluje na úrovni objektov.' },
]

// Cenník zodpovedá tomu, čo je naozaj vynútené v kóde (logic/plans.py):
// strop na počet projektov a členov tímu. Nič iné zamknuté nie je — kto by sem
// dopísal „PDF export len od Starteru", klamal by, lebo export má každý.
const PLANS = [
  {
    name: 'Free',
    price: '0 €',
    period: 'navždy',
    highlight: true,
    note: 'Jediný plán, ktorý je dnes spustený.',
    features: ['2 projekty', 'do 5 členov tímu', 'Všetky funkcie bez obmedzenia'],
    cta: 'Začať zadarmo',
    live: true,
  },
  {
    name: 'Starter',
    price: '7 €',
    period: '/ používateľ / mesiac',
    highlight: false,
    note: 'Pripravuje sa.',
    features: ['Neobmedzené projekty', 'do 15 členov tímu'],
    cta: 'Zatiaľ nedostupné',
    live: false,
  },
  {
    name: 'Team',
    price: '12 €',
    period: '/ používateľ / mesiac',
    highlight: false,
    note: 'Pripravuje sa.',
    features: ['Neobmedzené projekty', 'Neobmedzený tím'],
    cta: 'Zatiaľ nedostupné',
    live: false,
  },
]

const FAQ = [
  {
    q: 'Čím sa to líši od Trella alebo Monday?',
    a: 'Tie ti harmonogram nakreslia. Nodus ho aj prepočíta — nájde kritickú cestu a pri každej úlohe '
      + 'povie, o koľko dní sa môže posunúť bez toho, aby ohrozila termín. Rozšírené cloudové nástroje '
      + 'tento výpočet buď nemajú vôbec, alebo kritickú cestu len zafarbia bez uvedenia rezerv.',
  },
  {
    q: 'Prvé načítanie mi trvalo dlho.',
    a: 'Systém beží na bezplatnej úrovni cloudovej služby, ktorá server po dobe nečinnosti uspáva. '
      + 'Prvá požiadavka ho zobudí, čo trvá asi pol minúty. Ďalšie už reagujú normálne.',
  },
  {
    q: 'Musím vypĺňať tri odhady pri každej úlohe?',
    a: 'Nie. Stačí jedno trvanie a dostaneš kritickú cestu aj rezervy. Optimistický a pesimistický '
      + 'odhad sú voliteľné — bez nich sa len nepočíta PERT.',
  },
  {
    q: 'Čo sa stane s mojimi údajmi?',
    a: 'Každá organizácia má oddelený priestor a k cudzím údajom sa nedostaneš. Údaje si vieš '
      + 'kedykoľvek stiahnuť alebo nechať zmazať v nastaveniach.',
  },
]

export default function LandingPage() {
  const { dark, toggle } = useDarkMode()

  return (
    <div className="min-h-screen bg-bg dark:bg-bg-dark text-gray-900 dark:text-gray-100">
      {/* ── Navigácia ──────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 backdrop-blur bg-bg/80 dark:bg-bg-dark/80 border-b border-gray-200 dark:border-white/[0.07]">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          <NodusLogo variant="wordmark" size={28} />
          <div className="flex items-center gap-2">
            <a href="#ako-to-funguje" className="btn-ghost text-sm hidden md:inline-flex">Ako to funguje</a>
            <a href="#cennik" className="btn-ghost text-sm hidden md:inline-flex">Cenník</a>
            <button onClick={toggle} className="btn-ghost p-2" aria-label="Prepnúť tému">
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <Link to="/login" className="btn-ghost text-sm hidden sm:inline-flex">Prihlásiť sa</Link>
            <Link to="/signup" className="btn-primary text-sm">Vytvoriť účet</Link>
          </div>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[46rem] h-[46rem] bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-5 pt-16 pb-14 grid lg:grid-cols-2 gap-12 lg:gap-10 items-center">
          <div className="animate-fade-up">
            <span className="badge bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 mb-5">
              Projektový manažment na kritickej ceste
            </span>
            <h1 className="text-display font-bold">
              Vieš, ktoré úlohy naozaj{' '}
              <span className="text-brand-500">rozhodujú</span> o termíne?
            </h1>
            <p className="mt-5 text-lg text-gray-600 dark:text-gray-400 leading-relaxed">
              Nodus nerozdá len farebné pruhy. Spočíta kritickú cestu, rezervy a pravdepodobnosť,
              že termín stihneš — a po každej zmene trvania to prepočíta odznova.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-start gap-3">
              <Link to="/signup" className="btn-primary text-base px-6 py-3">
                Vyskúšať zadarmo <ArrowRight size={18} />
              </Link>
              <Link to="/login" className="btn-outline text-base px-6 py-3">Už mám účet</Link>
            </div>
            <p className="mt-4 text-xs text-gray-400">
              Bez platobnej karty · Po registrácii ti vieme založiť ukážkový projekt
            </p>
          </div>

          {/* Stránka doteraz o výpočte len hovorila. Toto ho ukazuje. */}
          <div className="animate-fade-up lg:[animation-delay:120ms]">
            <CpmShowcase />
          </div>
        </div>
      </section>

      {/* ── Odlišovač ──────────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-5 py-6">
        <div className="card p-6 sm:p-8 text-center">
          <p className="text-sm uppercase tracking-wide text-gray-400 mb-2">Prečo Nodus</p>
          <p className="text-lg sm:text-xl text-gray-700 dark:text-gray-300 leading-relaxed">
            Trello, Asana či Monday ti ukážu <strong>Ganttov graf</strong>. To je vizualizácia, nie analýza.
            Nodus navyše <strong className="text-brand-500">vypočíta kritickú cestu a rezervy</strong> —
            takže vieš, kde tlačiť a kde máš priestor.
          </p>
        </div>
      </section>

      {/* ── Ako to funguje ─────────────────────────────────────────────── */}
      <section id="ako-to-funguje" className="max-w-6xl mx-auto px-5 py-14 scroll-mt-20">
        <h2 className="text-title font-bold text-center mb-3">Tri kroky k výpočtu</h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-10">
          Od prázdneho projektu po kritickú cestu. Nič medzi tým nemusíš riešiť.
        </p>
        <ol className="grid sm:grid-cols-3 gap-5">
          {STEPS.map(({ icon: Icon, title, text }, i) => (
            <li key={title} className="card p-6 relative">
              <span className="absolute top-5 right-5 text-3xl font-bold text-gray-200 dark:text-white/[0.07] leading-none">
                {i + 1}
              </span>
              <div className="w-11 h-11 rounded-control bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center mb-4">
                <Icon className="text-brand-500" size={22} />
              </div>
              <h3 className="font-semibold text-lg mb-1.5">{title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ── Funkcie ────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-5 py-14">
        <h2 className="text-title font-bold text-center mb-3">Všetko pre riadenie projektu</h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-10">
          Od plánovania po odovzdanie — s matematickým jadrom.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card-interactive p-6">
              <div className="w-11 h-11 rounded-control bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center mb-4">
                <Icon className="text-brand-500" size={22} />
              </div>
              <h3 className="font-semibold text-lg mb-1.5">{title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Cenník ─────────────────────────────────────────────────────── */}
      <section id="cennik" className="max-w-6xl mx-auto px-5 py-14 scroll-mt-20">
        <h2 className="text-title font-bold text-center mb-3">Cenník</h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-10 max-w-xl mx-auto">
          Dnes je spustený iba plán Free a má všetky funkcie. Platené plány sú zatiaľ
          navrhnuté, nie spustené — líšiť sa budú len stropom na projekty a veľkosť tímu.
        </p>
        <div className="grid md:grid-cols-3 gap-6 items-start">
          {PLANS.map((p) => (
            <div
              key={p.name}
              className={`card p-7 relative ${p.highlight ? 'ring-2 ring-brand-500 md:-translate-y-2' : ''} ${!p.live ? 'opacity-75' : ''}`}
            >
              {p.highlight && (
                <span className="badge bg-brand-500 text-white absolute -top-3 left-1/2 -translate-x-1/2">
                  Dostupný teraz
                </span>
              )}
              <h3 className="font-semibold text-lg">{p.name}</h3>
              <div className="mt-3 mb-1 flex items-baseline gap-1">
                <span className="text-4xl font-bold">{p.price}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">{p.period}</span>
              </div>
              <p className="mt-2 text-xs text-gray-400">{p.note}</p>

              <ul className="mt-6 space-y-3">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    {p.live
                      ? <Check className="text-brand-500 shrink-0 mt-0.5" size={16} />
                      : <Minus className="text-gray-300 dark:text-gray-700 shrink-0 mt-0.5" size={16} />}
                    <span className="text-gray-700 dark:text-gray-300">{f}</span>
                  </li>
                ))}
              </ul>

              {p.live ? (
                <Link to="/signup" className="btn-primary mt-7 w-full">{p.cta}</Link>
              ) : (
                <span
                  className="btn-outline mt-7 w-full cursor-not-allowed opacity-60"
                  aria-disabled="true"
                >
                  {p.cta}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Časté otázky ───────────────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto px-5 py-14">
        <h2 className="text-title font-bold text-center mb-10">Časté otázky</h2>
        <div className="space-y-3">
          {FAQ.map(({ q, a }) => (
            <details key={q} className="card p-5 group">
              <summary className="flex items-center justify-between gap-4 cursor-pointer font-medium list-none">
                {q}
                <span className="text-brand-500 shrink-0 transition-transform duration-base ease-out group-open:rotate-45">
                  <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden>
                    <path d="M8 3v10M3 8h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </span>
              </summary>
              <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* ── Výzva ──────────────────────────────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-5 py-16">
        <div className="rounded-modal p-10 text-center bg-gradient-to-br from-brand-500 to-brand-700 shadow-raised">
          <h2 className="text-title font-bold text-white">Rozbehni svoj prvý projekt za dve minúty</h2>
          <p className="mt-3 text-white/80">
            Vytvor si organizáciu, alebo si nechaj založiť ukážkový projekt a pozri sa na hotový výpočet.
          </p>
          <Link
            to="/signup"
            className="mt-7 inline-flex items-center gap-2 bg-white text-brand-600 font-semibold px-6 py-3 rounded-control
                       hover:bg-brand-50 transition duration-fast ease-out"
          >
            Vytvoriť účet zadarmo <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ── Päta ───────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-200 dark:border-white/[0.07]">
        <div className="max-w-6xl mx-auto px-5 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-500 dark:text-gray-400">
          <NodusLogo variant="wordmark" size={22} />
          <p>© {new Date().getFullYear()} Nodus — projektový manažment na kritickej ceste</p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/podmienky" className="hover:text-brand-500 transition-colors duration-fast">Podmienky</Link>
            <Link to="/ochrana-osobnych-udajov" className="hover:text-brand-500 transition-colors duration-fast">Ochrana údajov</Link>
            <Link to="/login" className="hover:text-brand-500 transition-colors duration-fast">Prihlásiť sa</Link>
            <Link to="/signup" className="hover:text-brand-500 transition-colors duration-fast">Registrácia</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
