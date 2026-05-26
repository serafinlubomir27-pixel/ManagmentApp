# akhydroizol.sk — Fáza 1: Setup & Design System

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vytvoriť Next.js 15 projekt s Tailwind v4, design tokenmi, NavBarom a Footerom.

**Architecture:** Standalone Next.js 15 App Router projekt v novom adresári (mimo ManagmentApp). Tailwind v4 CSS variables pre design tokens. Komponenty rozdelené podľa zodpovednosti: `layout/`, `sections/`, `ui/`, `chatbot/`.

**Tech Stack:** Next.js 15, Tailwind CSS v4, TypeScript, DM Sans + Inter (next/font), Vitest + React Testing Library

**Spec:** `../specs/2026-05-26-akhydroizol-redesign-design.md`

---

## Súborová štruktúra (celý projekt)

```
akhydroizol/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── api/chat/route.ts
├── components/
│   ├── layout/
│   │   ├── NavBar.tsx
│   │   ├── Footer.tsx
│   │   └── MobileStickyBar.tsx
│   ├── sections/
│   │   ├── Hero.tsx
│   │   ├── TrustBar.tsx
│   │   ├── ProblemSection.tsx
│   │   ├── SolutionSection.tsx
│   │   ├── BeforeAfter.tsx
│   │   ├── ProcessSection.tsx
│   │   ├── StatsSection.tsx
│   │   ├── WhyUsSection.tsx
│   │   ├── GallerySection.tsx
│   │   ├── FAQSection.tsx
│   │   └── ContactSection.tsx
│   ├── ui/
│   │   ├── CountUp.tsx
│   │   └── SectionReveal.tsx
│   └── chatbot/
│       ├── ChatWidget.tsx
│       ├── ChatPanel.tsx
│       └── ChatMessage.tsx
├── lib/
│   ├── jsonld.ts
│   └── contact.ts
├── hooks/
│   ├── useCountUp.ts
│   └── useChat.ts
├── types/index.ts
└── __tests__/
    ├── lib/jsonld.test.ts
    ├── lib/contact.test.ts
    └── hooks/useCountUp.test.ts
```

---

## Task 1: Scaffold Next.js projektu

**Files:**
- Create: `akhydroizol/` (nový adresár mimo ManagmentApp)

- [ ] **Vytvor projekt**

```bash
cd ~/Projects   # alebo kde chceš mať projekt
npx create-next-app@latest akhydroizol \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
cd akhydroizol
```

- [ ] **Nainštaluj závislosti**

```bash
npm install framer-motion gsap @anthropic-ai/sdk resend \
  react-hook-form zod @hookform/resolvers \
  react-compare-image react-photo-album \
  yet-another-react-lightbox
npm install -D vitest @vitejs/plugin-react \
  @testing-library/react @testing-library/user-event \
  @testing-library/jest-dom jsdom
```

- [ ] **Nastav Vitest** — vytvor `vitest.config.ts`

```ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, '.') },
  },
})
```

- [ ] **Vytvor `vitest.setup.ts`**

```ts
import '@testing-library/jest-dom'
```

- [ ] **Pridaj test script do `package.json`**

```json
"scripts": {
  "test": "vitest",
  "test:run": "vitest run"
}
```

- [ ] **Overenie**

```bash
npm run test:run
```
Expected: `No test files found` (žiadna chyba)

- [ ] **Commit**

```bash
git init && git add -A
git commit -m "feat: scaffold Next.js 15 project with Vitest"
```

---

## Task 2: Design Tokens & Global CSS

**Files:**
- Modify: `app/globals.css`
- Modify: `tailwind.config.ts` (alebo `postcss.config.mjs`)
- Modify: `app/layout.tsx`

- [ ] **Prepíš `app/globals.css`**

```css
@import "tailwindcss";

@theme {
  --color-primary: #1A9AD6;
  --color-accent: #F5A623;
  --color-bg: #060a14;
  --color-surface: #0d1626;
  --color-surface-2: #111827;
  --color-problem: #dc2626;
  --color-solution: #16a34a;
  --color-ai: #7c3aed;

  --font-heading: var(--font-dm-sans);
  --font-body: var(--font-inter);
}

* {
  box-sizing: border-box;
}

body {
  background-color: var(--color-bg);
  color: #ffffff;
  font-family: var(--font-body), sans-serif;
}

h1, h2, h3, h4 {
  font-family: var(--font-heading), sans-serif;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Nastav fonty v `app/layout.tsx`**

```tsx
import type { Metadata } from 'next'
import { DM_Sans, Inter } from 'next/font/google'
import './globals.css'

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-dm-sans',
  weight: ['400', '500', '700', '800', '900'],
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  weight: ['400', '500', '600'],
})

export const metadata: Metadata = {
  title: 'Podrezávanie domov Topoľčany & okolie | AK Hydroizol',
  description: 'Hydroizolácia základov existujúcich stavieb. 20 rokov skúseností, 10-ročná záruka. Bezplatná obhliadka do 24h. Topoľčany, Partizánske, Trenčín, Nitra.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sk" className={`${dmSans.variable} ${inter.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add design tokens and global CSS"
```

---

## Task 3: NavBar

**Files:**
- Create: `components/layout/NavBar.tsx`

- [ ] **Vytvor `components/layout/NavBar.tsx`**

```tsx
'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'

const NAV_LINKS = [
  { label: 'Služby', href: '#solution' },
  { label: 'Ako to funguje', href: '#process' },
  { label: 'Realizácie', href: '#gallery' },
  { label: 'FAQ', href: '#faq' },
]

const TEL = '+421 900 000 000'

export default function NavBar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 transition-colors duration-300"
      style={{ height: 84, background: scrolled ? '#0d1626' : 'linear-gradient(to bottom, rgba(6,10,20,0.95), transparent)' }}
    >
      <div className="max-w-6xl mx-auto h-full px-8 flex items-center justify-between gap-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 rounded-lg bg-[#1A9AD6] flex items-center justify-center font-black text-white text-sm">
            AK
          </div>
          <div>
            <div className="font-black text-white text-[15px] leading-tight">AK Hydroizol</div>
            <div className="text-[10px] text-white/40 font-[family-name:var(--font-inter)]">
              Podrezávanie & hydroizolácia
            </div>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href}
              className="text-[13px] text-white/70 hover:text-white transition-colors font-[family-name:var(--font-inter)]">
              {l.label}
            </a>
          ))}
        </nav>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-4">
          <div className="text-right">
            <div className="text-[10px] text-white/40 font-[family-name:var(--font-inter)]">Zavolajte nám</div>
            <a href={`tel:${TEL.replace(/\s/g, '')}`}
              className="text-[19px] font-black text-[#F5A623] leading-tight">
              {TEL}
            </a>
          </div>
          <a href="#contact"
            className="bg-[#1A9AD6] text-white px-5 py-2.5 rounded-lg text-[13px] font-bold shrink-0">
            Získať ponuku
          </a>
        </div>

        {/* Mobile hamburger */}
        <button className="md:hidden text-white" onClick={() => setOpen(!open)}>
          {open ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-[#0d1626] border-t border-white/5 px-8 py-4 flex flex-col gap-4">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} onClick={() => setOpen(false)}
              className="text-white/70 text-[15px] font-[family-name:var(--font-inter)]">
              {l.label}
            </a>
          ))}
          <a href={`tel:${TEL.replace(/\s/g, '')}`} className="text-[#F5A623] font-black text-xl">
            {TEL}
          </a>
        </div>
      )}
    </header>
  )
}
```

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add NavBar with scroll effect and mobile menu"
```

---

## Task 4: Footer & MobileStickyBar

**Files:**
- Create: `components/layout/Footer.tsx`
- Create: `components/layout/MobileStickyBar.tsx`

- [ ] **Vytvor `components/layout/Footer.tsx`**

```tsx
const TEL = '+421 900 000 000'

const REGIONS = ['Topoľčany', 'Partizánske', 'Trenčín', 'Bánovce n/B', 'Nitra']
const SERVICES = ['Podrezávanie domov', 'Hydroizolácia základov', 'Hydroizolácia pivníc', 'Sanácia vlhkých stien']
const INFO = ['Ako to funguje', 'Realizácie', 'Časté otázky', 'Kontakt']

export default function Footer() {
  return (
    <footer className="bg-[#030710] border-t border-white/5 pt-12 pb-6">
      <div className="max-w-6xl mx-auto px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-[#1A9AD6] flex items-center justify-center font-black text-white text-xs">AK</div>
              <span className="font-black text-white">AK Hydroizol</span>
            </div>
            <p className="text-[12px] text-white/30 leading-relaxed mb-4 font-[family-name:var(--font-inter)]">
              Špecialisti na podrezávanie a hydroizoláciu základov existujúcich stavieb od roku 2004. Pôsobíme v regiónoch Topoľčany, Partizánske, Trenčín, Bánovce a Nitra.
            </p>
            <a href={`tel:${TEL.replace(/\s/g, '')}`} className="text-[18px] font-black text-[#F5A623]">{TEL}</a>
          </div>

          {/* Columns */}
          {[
            { title: 'Služby', items: SERVICES },
            { title: 'Regióny', items: REGIONS },
            { title: 'Informácie', items: INFO },
          ].map((col) => (
            <div key={col.title}>
              <h4 className="text-[11px] font-bold text-white/50 uppercase tracking-widest mb-4 font-[family-name:var(--font-inter)]">
                {col.title}
              </h4>
              <ul className="space-y-2">
                {col.items.map((item) => (
                  <li key={item}>
                    <a href="#" className="text-[13px] text-white/35 hover:text-white/70 transition-colors font-[family-name:var(--font-inter)]">
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-white/5 pt-5 flex flex-col md:flex-row justify-between items-center gap-3">
          <p className="text-[11px] text-white/20 font-[family-name:var(--font-inter)]">
            © 2025 AK Hydroizol · IČO: XXXXXXXX · Topoľčany
          </p>
          <div className="flex gap-5">
            {['Ochrana súkromia', 'GDPR', 'Cookies'].map((l) => (
              <a key={l} href="#" className="text-[11px] text-white/20 hover:text-white/50 transition-colors font-[family-name:var(--font-inter)]">{l}</a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}
```

- [ ] **Vytvor `components/layout/MobileStickyBar.tsx`**

```tsx
'use client'
const TEL = '+421 900 000 000'

export default function MobileStickyBar() {
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-[#0d1626] border-t border-[#1A9AD6]/20 px-4 py-3 flex gap-3">
      <a href={`tel:${TEL.replace(/\s/g, '')}`}
        className="flex-1 bg-[#F5A623] text-[#0d1626] font-black text-[14px] py-3 rounded-xl text-center">
        📞 {TEL}
      </a>
      <a href="#contact"
        className="flex-1 bg-[#1A9AD6] text-white font-bold text-[14px] py-3 rounded-xl text-center">
        Získať ponuku
      </a>
    </div>
  )
}
```

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add Footer and MobileStickyBar"
```

---

## Task 5: Základná page.tsx

**Files:**
- Modify: `app/page.tsx`

- [ ] **Prepíš `app/page.tsx`** (placeholder pre všetky sekcie)

```tsx
import NavBar from '@/components/layout/NavBar'
import Footer from '@/components/layout/Footer'
import MobileStickyBar from '@/components/layout/MobileStickyBar'

export default function Home() {
  return (
    <>
      <NavBar />
      <main>
        {/* Sekcie sa pridajú vo Fáze 2 */}
        <div className="min-h-screen flex items-center justify-center text-white/40">
          Fáza 1 hotová — sekcie prídu vo Fáze 2
        </div>
      </main>
      <Footer />
      <MobileStickyBar />
    </>
  )
}
```

- [ ] **Spusti dev server a over**

```bash
npm run dev
```
Otvor `http://localhost:3000` — musíš vidieť NavBar (transparent), footer a MobileStickyBar (na mobile).

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: wire up root layout with NavBar, Footer, MobileStickyBar"
```
