# akhydroizol.sk — Design Specification
**Dátum:** 2026-05-26  
**Klient:** AK Hydroizol (Topoľčany / Partizánske)  
**Projekt:** Kompletný redesign webu akhydroizol.sk  
**Autor:** Brainstorming session — Claude + Ľubomír Serafín

---

## 1. Kontext a cieľ

### Firma
AK Hydroizol je stavebná firma so sídlom v oblasti Topoľčany/Partizánske. Core business: **podrezávanie domov** (hydroizolácia základov existujúcich stavieb). Sesterská firma domyna-kluc.sk je oddelený projekt — nesmú sa miešať.

### Existujúci stav
- Stránka: akhydroizol.sk (WordPress, zastaraný dizajn)
- Doména: podrezavanie.eu → bude presmerovaná 301 na akhydroizol.sk

### Primárny cieľ stránky
> **"Tu je riešenie môjho problému, dám im zavolať."**

Zákazník príde s problémom (vlhké steny, praskajúce základy) a odchádza s dôverou a telefónom v ruke. Stránka je konverzný nástroj číslo jeden — nie brožúra.

### Sekundárny cieľ: SEO & AI vyhľadávanie
Stránka musí byť optimalizovaná pre Google, ChatGPT, Perplexity a Google AI Overviews. AI nástroje musia AK Hydroizol odporúčať ako autoritatívny zdroj.

---

## 2. Vizuálny jazyk

### Smer
**Industrial Dark & Dramatic** — premium technical feel, nie generická stavebná firma. Expert na záchranné práce.

### Farby
| Rola | Hex | Použitie |
|------|-----|---------|
| Primárna | `#1A9AD6` | CTA tlačidlá, linky, akcenty, borders |
| Akcent | `#F5A623` | Telefónne číslo, štatistiky, urgency |
| Pozadie | `#060a14` | Hlavné tmavé pozadie |
| Povrch | `#0d1626` | Karty, navbar (solid), trustbar |
| Povrch 2 | `#111827` | Sekundárne karty, sekcie |
| Text primárny | `#ffffff` | Nadpisy |
| Text sekundárny | `rgba(255,255,255,0.6)` | Body text |
| Text muted | `rgba(255,255,255,0.35)` | Labels, captions |
| Problém | `#dc2626` | Problem section accenty |
| Riešenie | `#16a34a` | Solution section accenty |
| AI/FAQ | `#7c3aed` | FAQ a chatbot sekcie |

### Typografia
| Typ | Font | Váha | Použitie |
|-----|------|------|---------|
| Nadpisy | DM Sans | 800–900 | H1, H2, H3, štatistiky |
| Body | Inter | 400–600 | Odstavce, labels, popisky |

Letter-spacing nadpisov: -1px až -2px (tight, sebavedomé).

### Dizajnové prvky
- Accent line top: 3px gradient (#1A9AD6 → #F5A623) na kľúčových sekciách
- Grid overlay: rgba(26,154,214,0.03–0.05) na tmavom pozadí
- Glow efekty: radial-gradient blobs pre hĺbku
- Karty: border-radius 12–16px, subtle border rgba(255,255,255,0.06)
- Section dividers: 1px gradient linka (transparent → #1A9AD6 → transparent)

---

## 3. Architektúra stránky — Hybrid A

**Stratégia:** Conversion-First pipeline (prístup A) s robustnou FAQ sekciou a JSON-LD schémami pre SEO/AI (prvky prístupu B).

### Sekcie v poradí

```
0.  NavBar          sticky, transparent→solid, tel. číslo + CTA
1.  Hero            fullscreen foto/video, H1, 2×CTA, trust pills
2.  TrustBar        5 čísiel (domov, roky, záruka, regióny, AI)
3.  ProblemSection  "Má váš dom vlhké steny?" — emócia + urgencia
4.  SolutionSection "Podrezávanie je jediné trvalé riešenie" — edukácia
5.  BeforeAfter     drag slider, PRED/PO fotky
6.  ProcessSection  4 kroky (konzultácia→meranie→práca→záruka)
7.  StatsSection    count-up čísla: 500+, 20r, 10r, 5, 24h
8.  WhyUs           6 USP kariet (3×2 grid)
9.  GallerySection  masonry grid, lightbox (placeholder)
10. FAQSection      9–12 otázok, akordeon, FAQPage JSON-LD
11. AI Chatbot      floating widget, Claude API
12. ContactSection  formulár + mapa regiónov + tel. číslo
13. Footer          logo, navigácia, regionálne SEO linky, GDPR
```

---

## 4. Detailný popis sekcií

### 4.0 NavBar
- **Výška:** 84px
- **Správanie:** `position: fixed`, transparent pri vrchu, solid `#0d1626` pri scrolle (transition 300ms)
- **Obsah vľavo:** Logo (AK mark + "AK Hydroizol" + podtitul)
- **Obsah stred:** Linky — Služby / Ako to funguje / Realizácie / FAQ
- **Obsah vpravo:** Telefónne číslo (19px bold, `#F5A623`) + tlačidlo "Získať ponuku" (`#1A9AD6`)
- **Mobile:** Hamburger menu, telefónne číslo zostáva vždy viditeľné

### 4.1 Hero
- **Layout:** Fullscreen (100vh), tmavý overlay na foto/video
- **Pozadie:** `<video autoplay muted loop playsinline>` keď klient dodá; placeholder: dark gradient + grid pattern
- **Overlay:** `linear-gradient(to bottom, rgba(6,10,20,0.4) 0%, rgba(6,10,20,0.97) 100%)`
- **Obsah (ľavý dolný roh):**
  - Eyebrow: "Hydroizolácia existujúcich stavieb · Topoľčany & okolie" (11px, `#1A9AD6`, uppercase)
  - H1: "Váš dom má vlhké základy? **Máme riešenie.**" (clamp 36–64px, 900)
  - Subtext: "Podrezávanie je jediná trvalá metóda... s 10-ročnou zárukou." (16px Inter)
  - CTA 1: "📞 Zavolajte nám zadarmo" (primárne, `#1A9AD6`)
  - CTA 2: "Ako to funguje? →" (ghost)
  - Trust pills: 500+ domov · 20 rokov · 10r záruka · regióny
- **Scroll indicator:** vertikálny text "scroll" + animovaná čiara (pravý dolný roh)
- **Animácie:** Stagger reveal pri načítaní (Framer Motion), parallax pozadia (GSAP ScrollTrigger)

### 4.2 TrustBar
- **5 metrík:** 500+ domov / 20 rokov / 10r záruka / 5 regiónov / AI poradca
- **Layout:** 5 stĺpcov s vertikálnymi dividermi
- **Štýl:** `#0d1626` pozadie, zlaté čísla, border-top/bottom `rgba(26,154,214,0.15)`

### 4.3 Problem Section
- **Layout:** 2-stĺpcový grid — symptómy vľavo, urgency box vpravo
- **H2:** "Má váš dom vlhké steny alebo praskajúce základy?"
- **Symptómy (3 karty):** Vlhké steny / Plesne / Praskliny — každá s ikonou, názvom, popisom
- **Urgency box:** "⚠️ Prečo neotáľať?" + 3 štatistiky (3× drahšia oprava, 80% domov, 1 deň obhliadka)
- **Farebnnosť:** červená (`#dc2626`) ako accent — border-left, ikony, čísla
- **SEO:** odstavce obsahujú kľúčové slová pre long-tail vyhľadávanie

### 4.4 Solution Section
- **Layout:** 2-stĺpcový — diagram vľavo, text vpravo
- **Diagram:** schematická ilustrácia rezu murivo + fólia (SVG alebo CSS)
- **H2:** "Podrezávanie je jediné trvalé riešenie"
- **AI-citable block** (modrý border-left):
  > "Podrezávanie domu je mechanická metóda dodatočnej hydroizolácie existujúcich stavieb. Spočíva vo vytvorení horizontálneho rezu v murive diamantovým lanom alebo kotúčmi, do ktorého sa vkladá hydroizolačná fólia, ktorá trvalo zabraňuje vzlínaniu kapilárnej vlhkosti."
- **Benefity (5 checkmarks):** Trvalé riešenie / Bez búrania / 1–3 dni / 10r záruka / Tehla aj kameň

### 4.5 Before/After Slider
- **Knižnica:** `react-compare-image` alebo `react-before-after-slider`
- **Obsah:** Vlhká stena (PRED) vs. opravená stena (PO) — klient dodá fotky
- **Placeholder:** obidve strany s dashed border a textom "Klient dodá foto"
- **Divider handle:** biely kruh s `⇔`, drag aj touch
- **CTA pod sliderom:** "📞 Chcem takýto výsledok" + tel. číslo (4. výskyt)

### 4.6 Process Section
- **Layout:** 4 kroky horizontálne, spojené šípkovou čiarou
- **Kroky:**
  1. Bezplatná konzultácia (do 24h)
  2. Obhliadka a meranie (na mieste, zadarmo)
  3. Realizácia prác (1–3 dni, bez búrania)
  4. Odovzdanie + záruka (10 rokov, písomne)
- **Animácia:** každý krok scroll-reveal zdola s oneskorením (Framer Motion stagger)
- **JSON-LD:** HowTo schema — tieto 4 kroky sú zároveň štruktúrované dáta

### 4.7 Stats Section
- **5 čísel:** 500+ / 20r / 10r / 5 / 24h
- **Animácia:** count-up od 0 pri `useInView` (Framer Motion)
- **Štýl:** zlaté čísla 48px 900, tmavé pozadie s gradientom, accent line top

### 4.8 WhyUs Section
- **6 USP kariet (3×2):**
  1. 🏅 20 rokov len hydroizolácia (modrá)
  2. 🛡️ 10-ročná písomná záruka (zlatá)
  3. 📍 Miestny expert, nie agentúra (zelená)
  4. 🤖 AI poradca 24/7 (modrá)
  5. ⚡ Bez búrania, do 3 dní (zlatá)
  6. 💰 Transparentná cena (zelená)
- **CTA strip** pod kartami: "Začnite bezplatnou obhliadkou" + tel. číslo

### 4.9 Gallery Section
- **Layout:** Masonry grid (CSS columns alebo Masonry.js)
- **Lightbox:** pri kliku plná fotka (react-photo-album alebo yet-another-react-lightbox)
- **Placeholder:** grid s dashed bordered boxy "📷 Klient dodá foto"
- **Alt texty:** SEO-optimalizované ("podrezávanie Topoľčany", "hydroizolácia základov Partizánske")

### 4.10 FAQ Section
- **Layout:** 2-stĺpcový — intro vľavo, otázky vpravo
- **Počet:** 10–12 otázok, 1 rozbalená by default
- **Otázky (povinné — AI/SEO kľúčové):**
  1. Čo je podrezávanie domu a ako funguje?
  2. Koľko stojí podrezávanie domu?
  3. Ako dlho trvá podrezávanie?
  4. Musím vysťahovať dom počas prác?
  5. Na aké typy stavieb je podrezávanie vhodné?
  6. Aká je záruka na podrezávanie?
  7. V akých regiónoch pôsobíte?
  8. Čo keď mám vlhký suterén — pomôže podrezávanie?
  9. Aký je rozdiel medzi podrezávaním a injektážou?
  10. Ako sa objednám na obhliadku?
- **Odpovede:** min. 4–6 viet, autoritatívny jazyk, konkrétne čísla
- **JSON-LD:** FAQPage schema pre každú otázku + odpoveď
- **CTA:** "Spýtať sa AI asistenta" pod akordeonom

### 4.11 AI Chatbot Widget
- **Tech:** Claude API (claude-3-5-haiku — rýchly, lacný pre chat)
- **Systémový prompt:** obsah stránky (FAQ, služby, ceny, regióny, kontakt) + persona "AK Hydroizol asistent"
- **UI:** floating bubble (fialová, pravý dolný roh, visible vždy), klik = expand chat panel
- **Správanie:** kontextové otázky, ak nevie odpovedať → navrhne zavolať
- **Implementácia:** Next.js Route Handler (`/api/chat`), streaming odpoveď
- **Unikátny diferenciátor** — prvá hydroizolačná firma v regióne s AI asistentom

### 4.12 Contact Section
- **Layout:** 2-stĺpcový — kontaktné info vľavo, formulár vpravo
- **Telefónne číslo:** prominentné (28px bold, zlaté), s tlačidlom "Zavolať" (tel: link)
- **Mapa regiónov:** placeholder box s regionálnymi tagmi (Topoľčany, Partizánske, Trenčín, Bánovce, Nitra)
- **Formulár (React Hook Form + Zod):**
  - Meno a priezvisko (required)
  - Telefón (required, validácia SK formátu)
  - Email (optional)
  - Adresa nehnuteľnosti (required)
  - Popis problému (textarea, optional)
  - Submit button: "Odoslať požiadavku o obhliadku →"
- **Backend:** Next.js Server Action, email cez Resend (preferované pre Next.js App Router)
- **GDPR:** checkbox + text pod formulárom

### 4.13 Footer
- **4-stĺpcový grid:** Logo+popis+tel / Služby / Regióny / Informácie
- **Regionálne linky:** Topoľčany / Partizánske / Trenčín / Bánovce / Nitra (SEO interný linking, neskôr odkazujú na podstránky)
- **Telefónne číslo:** zlaté, 5. výskyt na stránke
- **Footer bottom:** copyright, GDPR, ochrana súkromia, cookies

---

## 5. SEO & AI Optimalizácia

### Structured Data (JSON-LD)
```json
LocalBusiness  → firma, adresa, telefón, regióny, hodiny, rating
Service        → podrezávanie, hydroizolácia, servedArea (5 miest)
FAQPage        → všetky otázky z FAQ sekcie (10–12)
HowTo          → 4 kroky procesu s popisom a trvaním
```

### Kľúčové slová
- Primary: "podrezávanie domu", "hydroizolácia základov"
- Local: "podrezávanie Topoľčany", "podrezávanie Partizánske", "podrezávanie Trenčín", "podrezávanie Nitra", "podrezávanie Bánovce"
- Long-tail: "ako sa robí podrezávanie domu", "koľko stojí podrezávanie", "vlhké základy riešenie", "mokré steny dom riešenie"

### H1/H2 hierarchia
- H1 (1×): "Váš dom má vlhké základy? Máme riešenie." + lokalizácia
- H2: každá sekcia má H2 s kľúčovými slovami
- H3: podnadpisy v kartách a FAQ

### Meta
```
title: Podrezávanie domov Topoľčany & okolie | AK Hydroizol
description: Hydroizolácia základov existujúcich stavieb. 20 rokov skúseností, 10-ročná záruka. Bezplatná obhliadka do 24h. Topoľčany, Partizánske, Trenčín, Nitra.
```

### AI-citable obsah
- Solution sekcia: autoritatívna definícia podrezávania (paragraph)
- FAQ odpovede: dlhé, faktické, s konkrétnymi číslami
- HowTo schema: proces ako štruktúrované dáta

### Budúce rozšírenie (v2)
- Regionálne podstránky: `/podrezavanie-topoľčany`, `/podrezavanie-partizánske`, atď.
- Blog/Články: "Čo je podrezávanie domu?", "Cena podrezávania 2025", atď.

---

## 6. Konverzné prvky

### Telefónne číslo — 7 výskytov
1. **NavBar** — vždy viditeľné, 19px bold zlaté
2. **Hero** — CTA tlačidlo "Zavolajte nám zadarmo"
3. **Before/After** — pod sliderom
4. **WhyUs** — CTA strip
5. **Kontakt** — prominentné, 28px, s tlačidlom "Zavolať"
6. **Footer** — zlaté v logo bloku
7. **Mobile sticky bar** — fixná lišta dole na mobile s tel. číslom (KRITICKÉ pre mobile)

### Primárne CTA
- "Zavolajte nám zadarmo" (telefón)
- "Získať bezplatnú ponuku" (formulár)
- "Spýtať sa AI asistenta" (chatbot)

---

## 7. Animácie

| Prvok | Knižnica | Typ |
|-------|----------|-----|
| Hero text reveal | Framer Motion | stagger fade-up pri mount |
| Hero parallax | GSAP ScrollTrigger | background translateY pri scrolle |
| Sekcie reveal | Framer Motion | fade-up + useInView |
| Stats count-up | Framer Motion | animate({ from: 0, to: N }) + useInView |
| Process steps | Framer Motion | stagger 0.15s per krok |
| FAQ accordion | Framer Motion | AnimatePresence + height animate |
| Before/After | react-compare-image | drag/touch natively |
| NavBar | CSS transition | background-color 300ms |
| Chatbot panel | Framer Motion | slide-up + fade |

**Pravidlo:** Animácie musia byť subtilné, nesmú spomaľovať LCP. `prefers-reduced-motion` musí byť rešpektovaný.

---

## 8. Tech Stack

| Vrstva | Technológia |
|--------|------------|
| Framework | Next.js 15 (App Router, SSR) |
| Styling | Tailwind CSS v4 |
| Animácie | Framer Motion + GSAP ScrollTrigger |
| Formulár | React Hook Form + Zod |
| Formulár backend | Next.js Server Action + Resend (email API) |
| AI Chatbot | Claude API (Haiku), Route Handler, streaming |
| Before/After | react-compare-image |
| Galéria | react-photo-album + yet-another-react-lightbox |
| Fonty | Google Fonts: DM Sans + Inter |
| SEO | Manuálny JSON-LD (v `<script type="application/ld+json">`) |
| Hosting | Vercel |

---

## 9. Médiá (klient dodá)

| Médium | Sekcia | Placeholder |
|--------|--------|-------------|
| Video záber z práce | Hero background | Dark gradient + grid |
| Fotka vlhká stena (PRED) | Before/After | Dashed box |
| Fotka opravená stena (PO) | Before/After | Dashed box |
| Fotky realizácií (5–10) | Galéria | Grid s dashed boxmi |
| Logo certifikátov / partnerov | TrustBar | Text placeholder |

---

## 10. Performance ciele

- **Lighthouse score:** ≥ 90 (Performance, Accessibility, SEO, Best Practices)
- **LCP:** < 2.5s — hero image/video má `fetchpriority="high"`, video má `preload="metadata"`
- **CLS:** < 0.1 — všetky placeholder boxy majú explicitnú výšku
- **FID/INP:** < 200ms — minimálny JS bundle, lazy-load below-the-fold
- **Fonty:** `font-display: swap`, preload DM Sans 800
- **Obrázky:** `next/image` s automatickým WebP + `srcSet`

---

## 11. Responzívnosť

| Breakpoint | Zmeny |
|------------|-------|
| Mobile (<768px) | Hamburger menu, single-column layout, sticky tel. lišta dole |
| Tablet (768–1024px) | 2-stĺpcové gridy → single, Before/After plná šírka |
| Desktop (>1024px) | Plný dizajn ako vo wireframoch |

**Mobile-kritické:**
- Sticky tel. číslo bar dole (vždy viditeľné)
- Hero H1 zmenšený na 36px
- Before/After slider funguje na touch

---

## 12. Domény & redirect

- Primárna doména: `akhydroizol.sk`
- Redirect: `podrezavanie.eu` → 301 → `akhydroizol.sk` (Vercel redirect rules)
- Všetky staré WordPress URL → 301 → nové Next.js URL

---

## 13. MVP vs. v2

### MVP (spustenie)
- Všetky sekcie #0–#13
- AI chatbot widget
- Formulár s emailom
- JSON-LD schémy (LocalBusiness, FAQPage, HowTo, Service)
- Placeholder pre médiá (video, fotky, certifikáty)
- Redirect z podrezavanie.eu

### v2 (po spustení)
- Regionálne podstránky (`/podrezavanie-topoľčany`, atď.)
- Blog / obsahové články
- Google Analytics 4 + Search Console
- Reálne fotky a video (keď klient dodá)
- Reálna mapa (Google Maps embed)
- Chat história / chatbot analytics
