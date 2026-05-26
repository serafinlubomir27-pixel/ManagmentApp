# akhydroizol.sk — Fáza 2: Statické sekcie

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementovať všetky statické sekcie stránky — Hero až WhyUs + Gallery.

**Architecture:** Každá sekcia je izolovaný server komponent (bez 'use client'). Animácie prídu vo Fáze 5. Placeholder pre médiá (video, fotky).

**Tech Stack:** Next.js 15, Tailwind CSS v4, TypeScript

**Prerekvizita:** Fáza 1 dokončená.

---

## Task 6: Hero sekcia

**Files:**
- Create: `components/sections/Hero.tsx`
- Modify: `app/page.tsx`

- [ ] **Vytvor `components/sections/Hero.tsx`**

```tsx
const TEL = '+421 900 000 000'

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-end pb-20 overflow-hidden">
      {/* Pozadie — gradient + grid */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0f1e] via-[#1a2744] to-[#0a1220]" />
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage: `linear-gradient(rgba(26,154,214,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(26,154,214,0.04) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />
      {/* Overlay pre foto/video (keď klient dodá) */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#060a14]/40 via-transparent to-[#060a14]/97" />

      {/* VIDEO PLACEHOLDER — nahradiť: <video autoPlay muted loop playsInline className="absolute inset-0 w-full h-full object-cover" src="/video/hero.mp4" /> */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="border-2 border-dashed border-[#1A9AD6]/20 rounded-2xl px-10 py-6 text-center">
          <div className="text-4xl mb-2 opacity-30">🎬</div>
          <p className="text-[11px] text-[#1A9AD6]/40 uppercase tracking-widest font-[family-name:var(--font-inter)]">
            Video z práce — klient dodá
          </p>
        </div>
      </div>

      {/* Accent line top */}
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-transparent via-[#1A9AD6] to-[#F5A623]" />

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-8 w-full">
        {/* Eyebrow */}
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1.5 h-1.5 rounded-full bg-[#1A9AD6]" />
          <span className="text-[11px] font-semibold text-[#1A9AD6] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">
            Hydroizolácia existujúcich stavieb · Topoľčany & okolie
          </span>
        </div>

        {/* H1 */}
        <h1 className="text-[clamp(36px,5vw,64px)] font-black leading-[1.05] tracking-[-2px] text-white mb-5 max-w-3xl">
          Váš dom má<br />
          vlhké základy?<br />
          <span className="text-[#F5A623]">Máme riešenie.</span>
        </h1>

        {/* Subtext */}
        <p className="text-[16px] leading-relaxed text-white/60 font-[family-name:var(--font-inter)] mb-8 max-w-xl">
          Podrezávanie je jediná trvalá metóda hydroizolácie existujúcich stavieb.
          Bez búrania, bez dlhého čakania — s{' '}
          <strong className="text-white/85">10-ročnou zárukou</strong>.
        </p>

        {/* CTAs */}
        <div className="flex flex-wrap gap-3 mb-10">
          <a href={`tel:${TEL.replace(/\s/g, '')}`}
            className="bg-[#1A9AD6] text-white px-7 py-4 rounded-xl text-[15px] font-bold flex items-center gap-2">
            📞 Zavolajte nám zadarmo
          </a>
          <a href="#process"
            className="bg-white/6 border border-white/15 text-white/85 px-7 py-4 rounded-xl text-[15px] font-semibold">
            Ako to funguje? →
          </a>
        </div>

        {/* Trust pills */}
        <div className="flex flex-wrap gap-5">
          {[
            { icon: '✅', val: '500+', label: 'domov' },
            { icon: '🏅', val: '20 rokov', label: 'skúseností' },
            { icon: '🛡️', val: '10r záruka', label: 'na prácu' },
            { icon: '📍', val: 'Topoľčany', label: '· Partizánske · Trenčín' },
          ].map((p) => (
            <div key={p.val} className="flex items-center gap-2">
              <span>{p.icon}</span>
              <span className="text-[12px] text-white/50 font-[family-name:var(--font-inter)]">
                <strong className="text-white/85">{p.val}</strong> {p.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 right-12 flex flex-col items-center gap-1.5">
        <span className="text-[9px] tracking-[2px] uppercase text-white/30 [writing-mode:vertical-rl] font-[family-name:var(--font-inter)]">scroll</span>
        <div className="w-px h-10 bg-gradient-to-b from-transparent to-[#1A9AD6]/60" />
      </div>
    </section>
  )
}
```

- [ ] **Pridaj Hero do `app/page.tsx`**

```tsx
import Hero from '@/components/sections/Hero'
// ... ostatné importy z Fázy 1

export default function Home() {
  return (
    <>
      <NavBar />
      <main>
        <Hero />
        {/* ďalšie sekcie prídu */}
      </main>
      <Footer />
      <MobileStickyBar />
    </>
  )
}
```

- [ ] **Over v prehliadači** — `npm run dev` → `http://localhost:3000`
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add Hero section"
```

---

## Task 7: TrustBar

**Files:**
- Create: `components/sections/TrustBar.tsx`

- [ ] **Vytvor `components/sections/TrustBar.tsx`**

```tsx
const STATS = [
  { icon: '🏗️', val: '500+', label: 'zrealizovaných domov' },
  { icon: '📅', val: '20 rokov', label: 'na trhu' },
  { icon: '🛡️', val: '10 rokov', label: 'záruka na prácu' },
  { icon: '📍', val: '5 regiónov', label: 'Topoľčany · Partizánske · Trenčín' },
  { icon: '🤖', val: 'AI poradca', label: 'Opýtajte sa kedykoľvek' },
]

export default function TrustBar() {
  return (
    <div className="bg-[#0d1626] border-y border-[#1A9AD6]/15 px-8 py-5">
      <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-6">
        {STATS.map((s, i) => (
          <div key={s.val} className="flex items-center gap-2.5 flex-1 min-w-[140px]">
            {i > 0 && <div className="hidden lg:block w-px h-9 bg-white/6 mr-4" />}
            <span className="text-xl">{s.icon}</span>
            <div>
              <div className="text-[18px] font-black text-[#F5A623] leading-none">{s.val}</div>
              <div className="text-[11px] text-white/45 font-[family-name:var(--font-inter)] mt-0.5">{s.label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** za `<Hero />`
- [ ] **Commit** `git add -A && git commit -m "feat: add TrustBar"`

---

## Task 8: ProblemSection

**Files:**
- Create: `components/sections/ProblemSection.tsx`

- [ ] **Vytvor `components/sections/ProblemSection.tsx`**

```tsx
const SYMPTOMS = [
  {
    icon: '💧',
    title: 'Vlhké alebo mokré steny',
    desc: 'Voda preniká cez základy do muriva — viditeľné škvrny, olupujúca sa omietka a trvalá vlhkosť v interiéri.',
  },
  {
    icon: '🌿',
    title: 'Plesne a zatuchnutý zápach',
    desc: 'Vlhké prostredie je živnou pôdou pre plesne — zdravotné riziko pre celú rodinu, najmä deti a alergikov.',
  },
  {
    icon: '🔧',
    title: 'Praskajúce múry alebo podlahy',
    desc: 'Znak pohybu základov vplyvom zemnej vlhkosti — čím dlhšie čakáte, tým rozsiahlejšia a drahšia oprava.',
  },
]

export default function ProblemSection() {
  return (
    <section id="problem" className="py-20 px-8 bg-[#060a14] relative overflow-hidden">
      <div className="absolute top-[-100px] right-[-100px] w-[500px] h-[500px] rounded-full bg-[#dc2626]/6 blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16 items-center">
        {/* Vľavo */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#dc2626]" />
            <span className="text-[10px] font-bold text-[#dc2626] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Váš problém</span>
          </div>
          <h2 className="text-[40px] font-black leading-[1.1] tracking-[-1.5px] text-white mb-5">
            Má váš dom <span className="text-[#dc2626]">vlhké steny</span> alebo praskajúce základy?
          </h2>
          <p className="text-[16px] leading-relaxed text-white/60 font-[family-name:var(--font-inter)] mb-8">
            Vlhkosť v základoch nie je len estetický problém. Bez riešenia ničí statiku domu, spôsobuje plesne a zvyšuje náklady na vykurovanie.
          </p>
          <ul className="space-y-3">
            {SYMPTOMS.map((s) => (
              <li key={s.title} className="flex gap-3 p-3 rounded-xl bg-[#dc2626]/6 border border-[#dc2626]/12">
                <span className="text-[18px] mt-0.5 shrink-0">{s.icon}</span>
                <div>
                  <strong className="block text-[13px] text-white mb-1">{s.title}</strong>
                  <span className="text-[13px] text-white/55 leading-relaxed font-[family-name:var(--font-inter)]">{s.desc}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Urgency box */}
        <div className="relative bg-gradient-to-br from-[#1a0808] to-[#200e0e] border border-[#dc2626]/20 rounded-2xl p-8 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#dc2626] to-[#ef4444]" />
          <h3 className="text-[20px] font-black text-[#fca5a5] mb-3">⚠️ Prečo neotáľať?</h3>
          <p className="text-[14px] text-white/55 leading-relaxed font-[family-name:var(--font-inter)] mb-6">
            Vlhkosť v základoch je progresívny problém. Každý rok bez riešenia zvyšuje rozsah poškodenia — a cenu opravy.
          </p>
          {[
            { num: '3×', title: 'Drahšia oprava', desc: 'po 5 rokoch zanedbania oproti včasnej intervencii' },
            { num: '80%', title: 'Domov so suterénom', desc: 'v SR má problémy s vlhkosťou v základoch' },
            { num: '24h', title: 'Bezplatná obhliadka', desc: 'do 24 hodín — zistíme príčinu a navrhneme riešenie' },
          ].map((s) => (
            <div key={s.num} className="flex items-center gap-4 p-4 rounded-xl bg-[#dc2626]/8 mb-3 last:mb-0">
              <span className="text-[28px] font-black text-[#F5A623] shrink-0">{s.num}</span>
              <div>
                <strong className="block text-[13px] text-white/85 mb-0.5">{s.title}</strong>
                <span className="text-[12px] text-white/45 font-[family-name:var(--font-inter)]">{s.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** za `<TrustBar />`
- [ ] **Commit** `git add -A && git commit -m "feat: add ProblemSection"`

---

## Task 9: SolutionSection

**Files:**
- Create: `components/sections/SolutionSection.tsx`

- [ ] **Vytvor `components/sections/SolutionSection.tsx`**

```tsx
const BENEFITS = [
  'Trvalé riešenie — nie dočasná náplasť',
  'Bez búrania stien alebo podláh',
  'Hotovo za 1–3 dni podľa veľkosti domu',
  '10-ročná záruka na prácu',
  'Funguje na tehlovom aj kamennom murive',
]

export default function SolutionSection() {
  return (
    <section id="solution" className="py-20 px-8 bg-gradient-to-b from-[#060a14] via-[#071220] to-[#060a14] relative overflow-hidden">
      <div className="absolute bottom-[-100px] left-[-100px] w-[600px] h-[400px] rounded-full bg-[#1A9AD6]/7 blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16 items-start">
        {/* Diagram */}
        <div className="bg-gradient-to-br from-[#0a1f2e] to-[#0d2440] border border-[#1A9AD6]/15 rounded-2xl p-7 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[3px] rounded-t-2xl bg-gradient-to-r from-[#1A9AD6] to-[#0d6d9e]" />
          <p className="text-[13px] font-bold text-[#1A9AD6] mb-5 tracking-wide">🔬 Ako funguje podrezávanie</p>
          {/* SVG diagram muriva */}
          <svg viewBox="0 0 400 220" className="w-full mb-4" aria-label="Diagram podrezávania muriva">
            {/* Zem */}
            <rect x="0" y="160" width="400" height="60" fill="#1a4d1a" opacity="0.5" />
            {/* Základ */}
            <rect x="60" y="120" width="280" height="40" fill="#6b5230" opacity="0.6" />
            {/* Múr */}
            <rect x="100" y="40" width="200" height="80" fill="#8b7355" opacity="0.5" />
            {/* Rez */}
            <line x1="60" y1="120" x2="340" y2="120" stroke="#F5A623" strokeWidth="3" strokeDasharray="8,4" />
            {/* Fólia label */}
            <text x="200" y="112" textAnchor="middle" fill="#F5A623" fontSize="11" fontWeight="bold">— Hydroizolačná fólia —</text>
            {/* Vlhkosť */}
            <text x="30" y="180" fill="#1A9AD6" fontSize="20">💧</text>
            <text x="20" y="198" fill="rgba(255,255,255,0.3)" fontSize="9">vlhkosť</text>
          </svg>
          <p className="text-[11px] text-white/40 text-center leading-relaxed font-[family-name:var(--font-inter)]">
            Mechanický rez v murive → vloženie hydroizolačnej fólie → trvalá bariéra
          </p>
        </div>

        {/* Text */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#16a34a]" />
            <span className="text-[10px] font-bold text-[#16a34a] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Riešenie</span>
          </div>
          <h2 className="text-[36px] font-black leading-[1.1] tracking-[-1px] text-white mb-5">
            Podrezávanie je <span className="text-[#1A9AD6]">jediné trvalé riešenie</span>
          </h2>

          {/* AI-citable blok */}
          <div className="border-l-[3px] border-[#1A9AD6]/40 pl-5 py-3 bg-[#1A9AD6]/4 rounded-r-xl mb-6">
            <p className="text-[9px] font-bold text-[#1A9AD6]/60 uppercase tracking-[1.5px] mb-2 font-[family-name:var(--font-inter)]">
              🤖 Autoritatívna definícia
            </p>
            <p className="text-[14px] leading-[1.75] text-white/65 font-[family-name:var(--font-inter)]">
              Podrezávanie domu je mechanická metóda dodatočnej hydroizolácie existujúcich stavieb. Spočíva vo vytvorení horizontálneho rezu v murive diamantovým lanom alebo kotúčmi, do ktorého sa vkladá hydroizolačná fólia, ktorá trvalo zabraňuje vzlínaniu kapilárnej vlhkosti.
            </p>
          </div>

          <ul className="space-y-0">
            {BENEFITS.map((b) => (
              <li key={b} className="flex items-center gap-3 py-2.5 border-b border-white/5 last:border-0">
                <span className="text-[#16a34a] font-bold text-[15px]">✓</span>
                <span className="text-[14px] text-white/75 font-[family-name:var(--font-inter)]">{b}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`**
- [ ] **Commit** `git add -A && git commit -m "feat: add SolutionSection"`

---

## Task 10: ProcessSection

**Files:**
- Create: `components/sections/ProcessSection.tsx`

- [ ] **Vytvor `components/sections/ProcessSection.tsx`**

```tsx
const STEPS = [
  { num: 1, icon: '📞', title: 'Bezplatná konzultácia', desc: 'Zavoláte alebo vyplníte formulár. Do 24 hodín sa ozveme a dohodneme obhliadku — zadarmo, bez záväzkov.', badge: 'Do 24h', color: 'blue' },
  { num: 2, icon: '📐', title: 'Obhliadka a meranie', desc: 'Prídem osobne, zmeriam rozsah vlhkosti a typ muriva. Dostanete konkrétnu cenovú ponuku priamo na mieste.', badge: 'Zadarmo', color: 'blue' },
  { num: 3, icon: '🔧', title: 'Realizácia prác', desc: 'Diamantovým lanom prerežeme murivo, vložíme hydroizolačnú fóliu. Práce trvajú 1–3 dni, bez búrania.', badge: '1–3 dni', color: 'gold' },
  { num: 4, icon: '🛡️', title: 'Odovzdanie + záruka', desc: 'Prácu odovzdáme s písomnou zárukou na 10 rokov. Žiadna vlhkosť, žiadne starosti — garantovane.', badge: '10r záruka', color: 'green' },
]

const BADGE_STYLES: Record<string, string> = {
  blue: 'bg-[#1A9AD6]/15 text-[#1A9AD6]',
  gold: 'bg-[#F5A623]/15 text-[#F5A623]',
  green: 'bg-[#16a34a]/15 text-[#4ade80]',
}

export default function ProcessSection() {
  return (
    <section id="process" className="py-20 px-8 bg-[#060a14] relative overflow-hidden">
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `linear-gradient(rgba(26,154,214,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(26,154,214,0.03) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />
      <div className="max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-16">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#1A9AD6]" />
            <span className="text-[10px] font-bold text-[#1A9AD6] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Ako to funguje</span>
          </div>
          <h2 className="text-[38px] font-black tracking-[-1.5px] text-white mb-3">4 kroky k suchému domu</h2>
          <p className="text-[15px] text-white/45 font-[family-name:var(--font-inter)]">Od prvého kontaktu po hotovú prácu — jednoducho a transparentne</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 md:gap-0">
          {STEPS.map((step, i) => (
            <div key={step.num} className="relative flex flex-col items-center text-center px-5">
              {/* Connector */}
              {i < STEPS.length - 1 && (
                <div className="hidden md:block absolute top-8 left-[60%] right-0 h-[2px] bg-gradient-to-r from-[#1A9AD6]/50 to-[#1A9AD6]/15 z-0" />
              )}
              <div className="relative z-10 w-16 h-16 rounded-full bg-[#1A9AD6] flex items-center justify-center text-[22px] font-black text-white shadow-[0_0_0_8px_rgba(26,154,214,0.12),0_0_0_16px_rgba(26,154,214,0.05)] mb-5">
                {step.num}
              </div>
              <div className="text-[28px] mb-3">{step.icon}</div>
              <h3 className="text-[16px] font-black text-white mb-2">{step.title}</h3>
              <p className="text-[13px] text-white/50 leading-relaxed font-[family-name:var(--font-inter)] mb-3">{step.desc}</p>
              <span className={`text-[10px] font-bold px-3 py-1 rounded-full ${BADGE_STYLES[step.color]} font-[family-name:var(--font-inter)]`}>
                {step.badge}
              </span>
            </div>
          ))}
        </div>

        <p className="text-center mt-8 text-[12px] text-[#1A9AD6]/50 font-[family-name:var(--font-inter)]">
          Tieto kroky sú súčasťou HowTo JSON-LD schémy pre Google a AI vyhľadávanie
        </p>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`**
- [ ] **Commit** `git add -A && git commit -m "feat: add ProcessSection"`

---

## Task 11: StatsSection + CountUp hook

**Files:**
- Create: `hooks/useCountUp.ts`
- Create: `components/ui/CountUp.tsx`
- Create: `components/sections/StatsSection.tsx`
- Create: `__tests__/hooks/useCountUp.test.ts`

- [ ] **Napíš test pre useCountUp** — `__tests__/hooks/useCountUp.test.ts`

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useCountUp } from '@/hooks/useCountUp'

describe('useCountUp', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('starts at 0', () => {
    const { result } = renderHook(() => useCountUp({ target: 500, duration: 1000 }))
    expect(result.current).toBe(0)
  })

  it('reaches target after duration', () => {
    const { result } = renderHook(() => useCountUp({ target: 500, duration: 1000, start: true }))
    act(() => { vi.advanceTimersByTime(1100) })
    expect(result.current).toBe(500)
  })

  it('stays at 0 when start is false', () => {
    const { result } = renderHook(() => useCountUp({ target: 500, duration: 1000, start: false }))
    act(() => { vi.advanceTimersByTime(1100) })
    expect(result.current).toBe(0)
  })
})
```

- [ ] **Spusti — over FAIL**

```bash
npm run test:run -- __tests__/hooks/useCountUp.test.ts
```
Expected: FAIL — `Cannot find module '@/hooks/useCountUp'`

- [ ] **Implementuj `hooks/useCountUp.ts`**

```ts
import { useState, useEffect, useRef } from 'react'

interface Options {
  target: number
  duration?: number
  start?: boolean
}

export function useCountUp({ target, duration = 2000, start = true }: Options): number {
  const [count, setCount] = useState(0)
  const frameRef = useRef<number | null>(null)

  useEffect(() => {
    if (!start) return
    const startTime = performance.now()

    const tick = (now: number) => {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      // easeOutQuart
      const eased = 1 - Math.pow(1 - progress, 4)
      setCount(Math.round(eased * target))
      if (progress < 1) frameRef.current = requestAnimationFrame(tick)
    }

    frameRef.current = requestAnimationFrame(tick)
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current) }
  }, [target, duration, start])

  return count
}
```

- [ ] **Spusti — over PASS**

```bash
npm run test:run -- __tests__/hooks/useCountUp.test.ts
```
Expected: 3 passed

- [ ] **Vytvor `components/ui/CountUp.tsx`**

```tsx
'use client'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { useCountUp } from '@/hooks/useCountUp'

interface Props {
  target: number
  suffix?: string
  duration?: number
}

export default function CountUp({ target, suffix = '', duration = 2000 }: Props) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const count = useCountUp({ target, duration, start: inView })
  return <span ref={ref}>{count}{suffix}</span>
}
```

- [ ] **Vytvor `components/sections/StatsSection.tsx`**

```tsx
import CountUp from '@/components/ui/CountUp'

const STATS = [
  { icon: '🏗️', target: 500, suffix: '+', label: 'zrealizovaných domov', sub: 'od roku 2004' },
  { icon: '📅', target: 20, suffix: ' r', label: 'skúseností v odbore', sub: 'od roku 2004' },
  { icon: '🛡️', target: 10, suffix: ' r', label: 'záruka na každú prácu', sub: 'písomne' },
  { icon: '📍', target: 5, suffix: '', label: 'regiónov pôsobenia', sub: 'Topoľčany · Trenčín · Nitra' },
  { icon: '⏱️', target: 24, suffix: ' h', label: 'do odpovede', sub: 'obhliadka zadarmo' },
]

export default function StatsSection() {
  return (
    <section className="py-20 px-8 bg-gradient-to-br from-[#0a0f1e] via-[#0d1830] to-[#0a0f1e] relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#F5A623] to-[#1A9AD6]" />
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute left-[10%] top-1/2 -translate-y-1/2 w-80 h-80 rounded-full bg-[#1A9AD6]/7 blur-3xl" />
        <div className="absolute right-[10%] top-1/2 -translate-y-1/2 w-60 h-60 rounded-full bg-[#F5A623]/5 blur-3xl" />
      </div>
      <div className="max-w-6xl mx-auto relative z-10 grid grid-cols-2 md:grid-cols-5 gap-6">
        {STATS.map((s) => (
          <div key={s.label} className="text-center">
            <div className="text-2xl mb-2 opacity-90">{s.icon}</div>
            <div className="text-[48px] font-black text-[#F5A623] leading-none tracking-[-2px] mb-1">
              <CountUp target={s.target} suffix={s.suffix} />
            </div>
            <div className="text-[13px] text-white/50 font-[family-name:var(--font-inter)] mb-1">{s.label}</div>
            <div className="text-[11px] text-white/25 font-[family-name:var(--font-inter)]">{s.sub}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** (TrustBar, Problem, Solution, Process, Stats)
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add StatsSection with useCountUp hook (tested)"
```

---

## Task 12: WhyUsSection

**Files:**
- Create: `components/sections/WhyUsSection.tsx`

- [ ] **Vytvor `components/sections/WhyUsSection.tsx`**

```tsx
const TEL = '+421 900 000 000'

const CARDS = [
  { icon: '🏅', title: '20 rokov len hydroizolácia', desc: 'Podrezávanie je náš jediný odbor od roku 2004. Žiadne odbočky, žiadne experimenty — len jedna vec robená dokonale.', highlight: '500+ spokojných klientov', color: 'blue' },
  { icon: '🛡️', title: '10-ročná písomná záruka', desc: 'Každá realizácia je podložená písomnou zárukou na 10 rokov. Nie sľub ústne — dokument, ktorý môžete uplatniť.', highlight: 'Záruka vždy písomne', color: 'gold' },
  { icon: '📍', title: 'Miestny expert, nie agentúra', desc: 'Sme lokálna firma z regiónu Topoľčany. Poznáme miestne podmienky a môžeme prísť na obhliadku do 24 hodín.', highlight: 'Topoľčany · Partizánske · Trenčín', color: 'green' },
  { icon: '🤖', title: 'AI poradca 24/7', desc: 'Prvá firma v regióne s AI asistentom priamo na webe. Opýtajte sa kedykoľvek — okamžitá odpoveď, aj o polnoci.', highlight: 'Unikátny diferenciátor', color: 'blue' },
  { icon: '⚡', title: 'Bez búrania, do 3 dní', desc: 'Diamantové lano reže čisto, práce sú hotové za 1–3 dni a dom zostáva obývateľný počas celej realizácie.', highlight: 'Minimálny zásah do domu', color: 'gold' },
  { icon: '💰', title: 'Transparentná cena', desc: 'Cenovú ponuku dostanete po obhliadke — konkrétna suma, bez prekvapení. Obhliadka a konzultácia sú zadarmo.', highlight: 'Obhliadka zadarmo', color: 'green' },
]

const TOP: Record<string, string> = {
  blue: 'bg-[#1A9AD6]',
  gold: 'bg-[#F5A623]',
  green: 'bg-[#16a34a]',
}
const ICON_BG: Record<string, string> = {
  blue: 'bg-[#1A9AD6]/12',
  gold: 'bg-[#F5A623]/12',
  green: 'bg-[#16a34a]/12',
}
const HIGHLIGHT_COLOR: Record<string, string> = {
  blue: 'text-[#1A9AD6]',
  gold: 'text-[#F5A623]',
  green: 'text-[#4ade80]',
}

export default function WhyUsSection() {
  return (
    <section id="why-us" className="py-20 px-8 bg-[#07101f]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-14">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#F5A623]" />
            <span className="text-[10px] font-bold text-[#F5A623] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Prečo my</span>
          </div>
          <h2 className="text-[36px] font-black tracking-[-1px] text-white mb-3">Prečo si vybrať AK Hydroizol?</h2>
          <p className="text-[15px] text-white/40 font-[family-name:var(--font-inter)]">
            Nie sme generická stavebná firma — sme špecialisti na jeden problém, ktorý riešime dokonale
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-5 mb-8">
          {CARDS.map((c) => (
            <div key={c.title} className="relative bg-gradient-to-br from-[#0d1626] to-[#111e33] border border-white/6 rounded-2xl p-7 hover:border-[#1A9AD6]/25 transition-colors">
              <div className={`absolute top-0 left-6 right-6 h-[2px] rounded-b-sm ${TOP[c.color]}`} />
              <div className={`w-13 h-13 rounded-[14px] ${ICON_BG[c.color]} flex items-center justify-center text-2xl mb-4`}>
                {c.icon}
              </div>
              <h3 className="text-[17px] font-black text-white mb-2">{c.title}</h3>
              <p className="text-[13px] text-white/50 leading-relaxed font-[family-name:var(--font-inter)] mb-3">{c.desc}</p>
              <span className={`text-[11px] font-bold ${HIGHLIGHT_COLOR[c.color]} font-[family-name:var(--font-inter)]`}>
                → {c.highlight}
              </span>
            </div>
          ))}
        </div>

        {/* CTA strip */}
        <div className="bg-gradient-to-br from-[#0f2040] to-[#132840] border border-[#1A9AD6]/20 rounded-2xl p-7 flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <h3 className="text-[20px] font-black text-white mb-1">Presvedčení? Dajte nám vedieť.</h3>
            <p className="text-[14px] text-white/50 font-[family-name:var(--font-inter)]">Bezplatná obhliadka do 24 hodín — bez záväzkov, bez skrytých poplatkov</p>
          </div>
          <div className="flex items-center gap-4 shrink-0">
            <a href="#contact" className="bg-[#1A9AD6] text-white px-7 py-3.5 rounded-xl text-[14px] font-bold whitespace-nowrap">
              Získať bezplatnú ponuku
            </a>
            <div className="text-right">
              <span className="block text-[10px] text-white/35 font-[family-name:var(--font-inter)]">alebo zavolajte</span>
              <a href={`tel:${TEL.replace(/\s/g, '')}`} className="text-[17px] font-black text-[#F5A623]">{TEL}</a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`**
- [ ] **Commit** `git add -A && git commit -m "feat: add WhyUsSection"`

---

## Task 13: GallerySection (placeholder)

**Files:**
- Create: `components/sections/GallerySection.tsx`

- [ ] **Vytvor `components/sections/GallerySection.tsx`**

```tsx
const PLACEHOLDER_COUNT = 8

export default function GallerySection() {
  return (
    <section id="gallery" className="py-20 px-8 bg-[#060a14]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-white/30" />
            <span className="text-[10px] font-bold text-white/40 uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Realizácie</span>
          </div>
          <h2 className="text-[34px] font-black tracking-[-1px] text-white mb-3">Naše realizácie</h2>
          <p className="text-[15px] text-white/40 font-[family-name:var(--font-inter)]">Reálne fotky z dokončených zákaziek — klient dodá fotografie</p>
        </div>

        {/* Masonry grid — placeholder */}
        <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
          {Array.from({ length: PLACEHOLDER_COUNT }).map((_, i) => (
            <div
              key={i}
              className="break-inside-avoid border-2 border-dashed border-white/10 rounded-xl flex items-center justify-center text-center p-8"
              style={{ height: i % 3 === 0 ? 200 : i % 3 === 1 ? 160 : 240 }}
            >
              <div>
                <div className="text-3xl mb-2 opacity-20">📷</div>
                <p className="text-[11px] text-white/20 font-[family-name:var(--font-inter)] uppercase tracking-wide">Foto {i + 1}</p>
                <p className="text-[10px] text-white/15 font-[family-name:var(--font-inter)]">Klient dodá</p>
              </div>
            </div>
          ))}
        </div>
        <p className="text-center mt-6 text-[12px] text-white/20 font-[family-name:var(--font-inter)]">
          Po dodaní fotiek: nahradiť placeholder za react-photo-album + yet-another-react-lightbox
        </p>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** — všetky sekcie fázy 2 sú teraz na mieste
- [ ] **Over v prehliadači** — všetky sekcie musia byť viditeľné
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add GallerySection placeholder; complete phase 2 static sections"
```
