# akhydroizol.sk — Fáza 5: Animácie + Deploy

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pridať scroll-triggered animácie (Framer Motion + GSAP hero parallax), SectionReveal wrapper, mobile sticky bar, a nasadiť na Vercel s 301 redirectmi.

**Architecture:** `SectionReveal` je opakovateľný wrapper pre fade-up animáciu. GSAP sa inicializuje iba na klientovi (`useEffect`). Vercel `next.config.ts` obsahuje redirecty.

**Tech Stack:** Framer Motion, GSAP ScrollTrigger, Vercel CLI

**Prerekvizita:** Fáza 1–4 dokončená.

---

## Task 22: SectionReveal wrapper

**Files:**
- Create: `components/ui/SectionReveal.tsx`

- [ ] **Vytvor `components/ui/SectionReveal.tsx`**

```tsx
'use client'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'

interface Props {
  children: React.ReactNode
  delay?: number
  className?: string
}

export default function SectionReveal({ children, delay = 0, className }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-80px' })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 32 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
```

- [ ] **Obal každú sekciu v `app/page.tsx`**

```tsx
import SectionReveal from '@/components/ui/SectionReveal'

// Vzor — obaľ každú sekciu:
<SectionReveal delay={0}>
  <TrustBar />
</SectionReveal>
<SectionReveal delay={0}>
  <ProblemSection />
</SectionReveal>
// ... atď. pre každú sekciu
```

- [ ] **Over** — `npm run dev` → scrolluj → sekcie sa odkrývajú plynulo zdola nahor
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add SectionReveal scroll-triggered animation wrapper"
```

---

## Task 23: Hero stagger animácia (Framer Motion)

**Files:**
- Modify: `components/sections/Hero.tsx`

- [ ] **Pridaj `'use client'` a stagger animáciu do Hero**

Uprav `components/sections/Hero.tsx` — pridaj na vrch:

```tsx
'use client'
import { motion } from 'framer-motion'
```

Obaľ eyebrow, H1, subtext, CTAs a trust pills do `motion.div` so staggerom:

```tsx
// Nahraď existujúci obsah od eyebrow po trust pills:
<motion.div
  initial="hidden"
  animate="visible"
  variants={{
    visible: { transition: { staggerChildren: 0.12, delayChildren: 0.2 } },
    hidden: {},
  }}
>
  {[
    // eyebrow
    <div key="eyebrow" className="flex items-center gap-2 mb-5">
      <div className="w-1.5 h-1.5 rounded-full bg-[#1A9AD6]" />
      <span className="text-[11px] font-semibold text-[#1A9AD6] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">
        Hydroizolácia existujúcich stavieb · Topoľčany & okolie
      </span>
    </div>,
    // H1
    <h1 key="h1" className="text-[clamp(36px,5vw,64px)] font-black leading-[1.05] tracking-[-2px] text-white mb-5 max-w-3xl">
      Váš dom má<br />vlhké základy?<br /><span className="text-[#F5A623]">Máme riešenie.</span>
    </h1>,
    // subtext
    <p key="sub" className="text-[16px] leading-relaxed text-white/60 font-[family-name:var(--font-inter)] mb-8 max-w-xl">
      Podrezávanie je jediná trvalá metóda hydroizolácie existujúcich stavieb.
      Bez búrania — s <strong className="text-white/85">10-ročnou zárukou</strong>.
    </p>,
    // CTAs
    <div key="ctas" className="flex flex-wrap gap-3 mb-10">
      <a href={`tel:${TEL.replace(/\s/g,'')}`} className="bg-[#1A9AD6] text-white px-7 py-4 rounded-xl text-[15px] font-bold flex items-center gap-2">
        📞 Zavolajte nám zadarmo
      </a>
      <a href="#process" className="bg-white/6 border border-white/15 text-white/85 px-7 py-4 rounded-xl text-[15px] font-semibold">
        Ako to funguje? →
      </a>
    </div>,
  ].map((el, i) => (
    <motion.div
      key={i}
      variants={{
        hidden: { opacity: 0, y: 24 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.22,1,0.36,1] } },
      }}
    >
      {el}
    </motion.div>
  ))}
</motion.div>
```

- [ ] **Over** — `npm run dev` → obnoviť stránku → hero obsah sa postupne odkrýva
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add Hero stagger reveal animation"
```

---

## Task 24: GSAP Hero parallax

**Files:**
- Create: `components/sections/HeroParallax.tsx` (client wrapper pre GSAP)

- [ ] **Vytvor `components/sections/HeroParallax.tsx`**

```tsx
'use client'
import { useEffect, useRef } from 'react'

export default function HeroParallax() {
  const bgRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Lazy-load GSAP len na klientovi
    let ctx: { revert: () => void } | null = null

    import('gsap').then(({ gsap }) =>
      import('gsap/ScrollTrigger').then(({ ScrollTrigger }) => {
        gsap.registerPlugin(ScrollTrigger)

        if (bgRef.current) {
          ctx = gsap.context(() => {
            gsap.to(bgRef.current, {
              yPercent: 30,
              ease: 'none',
              scrollTrigger: {
                trigger: bgRef.current,
                start: 'top top',
                end: 'bottom top',
                scrub: true,
              },
            })
          })
        }
      })
    )

    return () => ctx?.revert()
  }, [])

  return (
    <div
      ref={bgRef}
      className="absolute inset-0 will-change-transform"
      style={{
        background: 'linear-gradient(135deg, #0a0f1e 0%, #1a2744 40%, #0a1220 100%)',
      }}
    />
  )
}
```

- [ ] **Vlož HeroParallax do `components/sections/Hero.tsx`**

Nahraď statický bg div:

```tsx
// Zmaž:
// <div className="absolute inset-0 bg-gradient-to-br from-[#0a0f1e] via-[#1a2744] to-[#0a1220]" />

// Pridaj:
import HeroParallax from './HeroParallax'
// ...
<HeroParallax />
```

- [ ] **Over** — `npm run dev` → scrolluj → hero pozadie sa pohybuje pomalšie ako obsah (parallax)
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add GSAP ScrollTrigger parallax to Hero background"
```

---

## Task 25: ProcessSection stagger animácia

**Files:**
- Modify: `components/sections/ProcessSection.tsx`

- [ ] **Pridaj `'use client'` a stagger na kroky**

```tsx
'use client'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'

// V returne — obaľ steps-row div:
const ref = useRef<HTMLDivElement>(null)
const inView = useInView(ref, { once: true, margin: '-60px' })

// ...

<div ref={ref} className="grid grid-cols-1 md:grid-cols-4 gap-6 md:gap-0">
  {STEPS.map((step, i) => (
    <motion.div
      key={step.num}
      initial={{ opacity: 0, y: 30 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay: i * 0.15, ease: [0.22,1,0.36,1] }}
      className="relative flex flex-col items-center text-center px-5"
    >
      {/* existujúci obsah kroku */}
    </motion.div>
  ))}
</div>
```

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add stagger animation to ProcessSection steps"
```

---

## Task 26: Meta tags + sitemap

**Files:**
- Modify: `app/layout.tsx`
- Create: `app/sitemap.ts`
- Create: `app/robots.ts`

- [ ] **Rozšír metadata v `app/layout.tsx`**

```tsx
export const metadata: Metadata = {
  title: {
    default: 'Podrezávanie domov Topoľčany & okolie | AK Hydroizol',
    template: '%s | AK Hydroizol',
  },
  description: 'Hydroizolácia základov existujúcich stavieb. 20 rokov skúseností, 10-ročná záruka. Bezplatná obhliadka do 24h. Topoľčany, Partizánske, Trenčín, Nitra.',
  keywords: ['podrezávanie domov', 'hydroizolácia základov', 'podrezávanie Topoľčany', 'podrezávanie Partizánske', 'vlhké základy riešenie'],
  openGraph: {
    title: 'AK Hydroizol — Podrezávanie domov',
    description: 'Hydroizolácia základov existujúcich stavieb. 20 rokov skúseností.',
    url: 'https://akhydroizol.sk',
    siteName: 'AK Hydroizol',
    locale: 'sk_SK',
    type: 'website',
  },
  alternates: { canonical: 'https://akhydroizol.sk' },
  robots: { index: true, follow: true },
}
```

- [ ] **Vytvor `app/sitemap.ts`**

```ts
import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: 'https://akhydroizol.sk',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 1,
    },
  ]
}
```

- [ ] **Vytvor `app/robots.ts`**

```ts
import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: '*', allow: '/' },
    sitemap: 'https://akhydroizol.sk/sitemap.xml',
  }
}
```

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add meta tags, sitemap, robots.txt"
```

---

## Task 27: Vercel deploy + redirecty

**Files:**
- Modify: `next.config.ts`
- Create: `vercel.json`

- [ ] **Nastav redirecty v `next.config.ts`**

```ts
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async redirects() {
    return [
      // podrezavanie.eu → akhydroizol.sk (301 permanent)
      {
        source: '/:path*',
        has: [{ type: 'host', value: 'podrezavanie.eu' }],
        destination: 'https://akhydroizol.sk/:path*',
        permanent: true,
      },
      // www → non-www
      {
        source: '/:path*',
        has: [{ type: 'host', value: 'www.akhydroizol.sk' }],
        destination: 'https://akhydroizol.sk/:path*',
        permanent: true,
      },
    ]
  },
}

export default nextConfig
```

- [ ] **Spusti build lokálne — over žiadne chyby**

```bash
npm run build
```
Expected: `✓ Compiled successfully` — žiadne TypeScript ani build errory

- [ ] **Deployni na Vercel**

```bash
npx vercel --prod
```

Alebo cez Vercel Dashboard:
1. Import GitHub repo
2. Framework: Next.js (auto-detect)
3. Environment variables: `RESEND_API_KEY`, `CONTACT_EMAIL`, `ANTHROPIC_API_KEY`
4. Deploy

- [ ] **Nastav domény vo Vercel Dashboard**
  - Pridaj `akhydroizol.sk` ako primary domain
  - Pridaj `podrezavanie.eu` → redirect na `akhydroizol.sk`
  - DNS: u registrátora nastav A record → Vercel IP (76.76.21.21)

- [ ] **Over redirecty**

```bash
curl -I https://podrezavanie.eu
```
Expected: `HTTP/2 301` + `location: https://akhydroizol.sk/`

- [ ] **Over Lighthouse** — `https://akhydroizol.sk` → DevTools → Lighthouse → over ≥ 90

- [ ] **Over JSON-LD** — https://search.google.com/test/rich-results → vlož URL → over LocalBusiness, FAQPage, HowTo

- [ ] **Commit & tag**

```bash
git add -A && git commit -m "feat: add Vercel redirects and build config"
git tag v1.0.0
git push origin main --tags
```

---

## Task 28: Záverečná kontrola

- [ ] **Spusti všetky testy**

```bash
npm run test:run
```
Expected: všetky testy PASS (useCountUp × 3, contactSchema × 5, jsonld × 8, useChat × 3)

- [ ] **Build check**

```bash
npm run build && npm run start
```
Over: `http://localhost:3000` — plná stránka funguje

- [ ] **Mobile test** — DevTools → Toggle Device → iPhone 14 → over:
  - Sticky bar dole (tel. číslo)
  - Hamburger menu
  - Hero H1 čitateľné
  - Before/After slider funguje na touch
  - FAQ akordeon funguje
  - Formulár funkčný

- [ ] **Skontroluj všetky tel. čísla** — 7 výskytov musí byť klikateľných (`tel:` link)

- [ ] **Over chatbot** — opýtaj sa: "Koľko stojí podrezávanie?" → streaming odpoveď do 3s

- [ ] **Finálny commit**

```bash
git add -A && git commit -m "chore: final QA pass — phase 5 complete"
```

---

## Prehľad testov (všetky fázy)

| Test file | Čo testuje | Počet testov |
|-----------|-----------|-------------|
| `__tests__/hooks/useCountUp.test.ts` | Count-up hook | 3 |
| `__tests__/lib/contact.test.ts` | Zod schema validácia | 5 |
| `__tests__/lib/jsonld.test.ts` | JSON-LD generátory | 8 |
| `__tests__/hooks/useChat.test.ts` | Chat hook stav | 3 |
| **Celkom** | | **19** |
