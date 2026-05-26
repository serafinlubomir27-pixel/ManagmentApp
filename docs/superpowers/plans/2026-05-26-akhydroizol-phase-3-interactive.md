# akhydroizol.sk — Fáza 3: Interaktívne komponenty

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Before/After slider, FAQ akordeon, galéria s lightboxom a kontaktný formulár s odosielaním cez Resend.

**Architecture:** Komponenty označené `'use client'`. Formulár používa Next.js Server Action pre odosielanie emailu. Zod validácia zdieľaná medzi klientom a serverom.

**Tech Stack:** react-compare-image, react-photo-album, yet-another-react-lightbox, React Hook Form, Zod, Resend, Next.js Server Actions

**Prerekvizita:** Fáza 1 + Fáza 2 dokončená.

---

## Task 14: Before/After Slider

**Files:**
- Create: `components/sections/BeforeAfter.tsx`

- [ ] **Vytvor `components/sections/BeforeAfter.tsx`**

```tsx
'use client'
import ReactCompareImage from 'react-compare-image'

const TEL = '+421 900 000 000'

// Placeholder SVG dáta URI — nahradiť reálnymi fotkami
const BEFORE_PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='500'%3E%3Crect fill='%231a0f0a' width='800' height='500'/%3E%3Ctext x='400' y='240' text-anchor='middle' fill='rgba(255,255,255,0.2)' font-size='18' font-family='sans-serif'%3EPRED — Vlhká stena%3C/text%3E%3Ctext x='400' y='270' text-anchor='middle' fill='rgba(255,255,255,0.1)' font-size='13' font-family='sans-serif'%3EKlient dodá fotku%3C/text%3E%3C/svg%3E"
const AFTER_PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='800' height='500'%3E%3Crect fill='%230a1a0d' width='800' height='500'/%3E%3Ctext x='400' y='240' text-anchor='middle' fill='rgba(255,255,255,0.2)' font-size='18' font-family='sans-serif'%3EPO — Opravená stena%3C/text%3E%3Ctext x='400' y='270' text-anchor='middle' fill='rgba(255,255,255,0.1)' font-size='13' font-family='sans-serif'%3EKlient dodá fotku%3C/text%3E%3C/svg%3E"

export default function BeforeAfter() {
  return (
    <section id="before-after" className="py-20 px-8 bg-[#08101e] relative overflow-hidden">
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage: `linear-gradient(rgba(26,154,214,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(26,154,214,0.03) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />
      <div className="max-w-5xl mx-auto relative z-10">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#1A9AD6]" />
            <span className="text-[10px] font-bold text-[#1A9AD6] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Výsledky práce</span>
          </div>
          <h2 className="text-[36px] font-black tracking-[-1px] text-white mb-3">Pred a po podrezávaní</h2>
          <p className="text-[15px] text-white/50 font-[family-name:var(--font-inter)]">
            Potiahnite slider a porovnajte výsledok — reálne fotky od klientov
          </p>
        </div>

        {/* Slider */}
        <div className="rounded-2xl overflow-hidden border border-[#1A9AD6]/20 shadow-[0_32px_80px_rgba(0,0,0,0.6)] mb-6 cursor-ew-resize">
          <ReactCompareImage
            leftImage={BEFORE_PLACEHOLDER}
            rightImage={AFTER_PLACEHOLDER}
            leftImageLabel="PRED"
            rightImageLabel="PO"
            sliderLineColor="#ffffff"
            sliderLineWidth={2}
            handle={
              <div className="w-11 h-11 bg-white rounded-full flex items-center justify-center shadow-lg text-[#0d1626] font-black text-lg select-none">
                ⇔
              </div>
            }
          />
        </div>

        <p className="text-center text-[13px] text-white/35 font-[family-name:var(--font-inter)] mb-8">
          ← Potiahnite slider myšou alebo prstom → &nbsp;|&nbsp;{' '}
          <span className="text-[#1A9AD6]">Reálne fotky z realizácií</span>
        </p>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-5">
          <a href="#contact" className="bg-[#1A9AD6] text-white px-8 py-4 rounded-xl text-[15px] font-bold">
            📞 Chcem takýto výsledok
          </a>
          <div className="text-center">
            <span className="block text-[11px] text-white/35 font-[family-name:var(--font-inter)]">alebo zavolajte priamo</span>
            <a href={`tel:${TEL.replace(/\s/g, '')}`} className="text-[20px] font-black text-[#F5A623]">{TEL}</a>
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** za SolutionSection (pred ProcessSection)
- [ ] **Over slider** — musí byť drag funkčný na desktop aj touch
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add BeforeAfter slider (react-compare-image)"
```

---

## Task 15: FAQ sekcia s akordeonom

**Files:**
- Create: `components/sections/FAQSection.tsx`

- [ ] **Vytvor `components/sections/FAQSection.tsx`**

```tsx
'use client'
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

const FAQ_ITEMS = [
  {
    q: 'Čo je podrezávanie domu a ako funguje?',
    a: 'Podrezávanie domu je mechanická metóda dodatočnej hydroizolácie existujúcich stavieb. Diamantovým lanom alebo kotúčmi vytvoríme horizontálny rez v murive, do ktorého vložíme hydroizolačnú fóliu. Táto fólia trvalo zabraňuje vzlínaniu kapilárnej vlhkosti zo základov do stien. Výsledkom je trvalé suché murivo — nie dočasná náplasť. Metóda je overená desaťročiami a je odporúčaná aj stavebníckymi inšpekciami.',
  },
  {
    q: 'Koľko stojí podrezávanie domu?',
    a: 'Cena závisí od dĺžky muriva, hrúbky stien a typu materiálu. Pre bežný rodinný dom s obvodom 40 metrov sa cena pohybuje od 2 000 do 5 000 €. Presnú cenovú ponuku dostanete po bezplatnej obhliadke na mieste — žiadne skryté poplatky, žiadne prekvapenia. Obhliadka je zadarmo a bez záväzkov.',
  },
  {
    q: 'Ako dlho trvá podrezávanie?',
    a: 'Pre bežný rodinný dom trvajú práce 1 až 3 pracovné dni. Závisí to od dĺžky muriva a hrúbky stien. Väčšie domy alebo zložitejšie múry môžu trvať dlhšie. Počas prác je dom plne obývateľný — nepotrebujete sa vysťahovať.',
  },
  {
    q: 'Musím vysťahovať dom počas prác?',
    a: 'Nie. Podrezávanie prebieha z exteriéru alebo suterénu a dom zostáva počas celej realizácie obývateľný. Práce sú síce hlučné (vrtanie a rezanie), ale nevyžadujú vypratanie nábytku ani presťahovanie. Mierne obmedzenie prístupu do oblasti práce trvá len počas aktívnej fázy rezania.',
  },
  {
    q: 'Na aké typy stavieb je podrezávanie vhodné?',
    a: 'Podrezávanie je vhodné pre tehlové, kamenné aj zmiešané murivo. Funguje na rodinných domoch, bytových domoch, historických stavbách aj priemyselných budovách. Nie je vhodné pre monolitické betónové konštrukcie. Typ muriva určíme pri bezplatnej obhliadke.',
  },
  {
    q: 'Aká je záruka na podrezávanie?',
    a: 'Na každú realizáciu poskytujeme 10-ročnú písomnú záruku. Záruka je doložená zmluvou — nie len ústnym sľubom. Zahŕňa tesnotu hydroizolačnej fólie a správnosť realizácie. V prípade akejkoľvek reklamácie reagujeme do 48 hodín.',
  },
  {
    q: 'V akých regiónoch pôsobíte?',
    a: 'Pôsobíme v regiónoch Topoľčany, Partizánske, Bánovce nad Bebravou, Trenčín a Nitra. Na obhliadku prídem osobne do 24 hodín od dohody. Ak ste z iného regiónu, kontaktujte nás — pre väčšie zákazky vieme dojednať výjazd aj ďalej.',
  },
  {
    q: 'Aký je rozdiel medzi podrezávaním a injektážou?',
    a: 'Podrezávanie je mechanická metóda — fyzicky vkladáme fóliu do muriva. Injektáž (chemická hydroizolácia) vstrekuje chemické látky do muriva. Podrezávanie je spoľahlivejšie a dlhodobejšie — fólia je fyzická bariéra, ktorá sa nedegraduje. Injektáž je lacnejšia, ale menej trvanlivá a závisí od poréznosti muriva. Odporúčame podrezávanie ako trvalé riešenie.',
  },
  {
    q: 'Čo keď mám vlhký suterén — pomôže podrezávanie?',
    a: 'Závisí od príčiny vlhkosti. Ak je príčinou vzlínajúca kapilárna vlhkosť zo základov, podrezávanie je ideálne riešenie. Ak ide o tlakovú vodu (napr. podzemná voda pri suteréne), potrebujete iný typ hydroizolácie. Príčinu určíme pri bezplatnej obhliadke a navrhneme správne riešenie.',
  },
  {
    q: 'Ako sa objednám na obhliadku?',
    a: 'Zavolajte nám na +421 900 000 000 alebo vyplňte formulár na tejto stránke. Ozveme sa do 24 hodín a dohodneme termín obhliadky. Obhliadka je bezplatná, trvá cca 30–60 minút a na jej konci dostanete konkrétnu cenovú ponuku.',
  },
]

export default function FAQSection() {
  const [open, setOpen] = useState<number | null>(0)

  return (
    <section id="faq" className="py-20 px-8 bg-gradient-to-b from-[#060a14] via-[#080e1c] to-[#060a14] relative overflow-hidden">
      <div className="absolute top-[-200px] right-[-200px] w-[600px] h-[600px] rounded-full bg-[#7c3aed]/6 blur-3xl pointer-events-none" />

      <div className="max-w-6xl mx-auto grid md:grid-cols-[300px_1fr] gap-16 relative z-10">
        {/* Vľavo */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#7c3aed]" />
            <span className="text-[10px] font-bold text-[#7c3aed] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Časté otázky</span>
          </div>
          <h2 className="text-[36px] font-black leading-[1.1] tracking-[-1px] text-white mb-4">
            Odpovede na vaše otázky
          </h2>
          <p className="text-[14px] text-white/45 font-[family-name:var(--font-inter)] leading-relaxed mb-6">
            Každá odpoveď je napísaná tak, aby vám skutočne pomohla — konkrétne, bez zbytočného žargónu.
          </p>
          <div className="bg-[#7c3aed]/6 border border-[#7c3aed]/15 rounded-xl p-4">
            <p className="text-[12px] text-white/35 font-[family-name:var(--font-inter)] leading-relaxed">
              <strong className="text-[#7c3aed]/80">SEO & AI:</strong> Otázky a odpovede sú súčasťou FAQPage JSON-LD schémy — ChatGPT, Perplexity a Google AI Overviews ich priamo citujú.
            </p>
          </div>
        </div>

        {/* Vpravo — akordeon */}
        <div className="space-y-2">
          {FAQ_ITEMS.map((item, i) => (
            <div
              key={i}
              className={`border rounded-xl overflow-hidden transition-colors ${
                open === i ? 'border-[#7c3aed]/25 bg-[#7c3aed]/3' : 'border-white/6 bg-white/2'
              }`}
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full px-5 py-4 flex items-center justify-between gap-4 text-left"
              >
                <span className={`text-[14px] font-bold leading-snug ${open === i ? 'text-white' : 'text-white/85'} font-[family-name:var(--font-heading)]`}>
                  {item.q}
                </span>
                <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[13px] shrink-0 transition-transform ${open === i ? 'bg-[#7c3aed]/20 rotate-180' : 'bg-white/5'}`}>
                  ▼
                </span>
              </button>
              <AnimatePresence initial={false}>
                {open === i && (
                  <motion.div
                    key="answer"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25, ease: 'easeInOut' }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 pb-4 pt-1 border-t border-white/4">
                      <p className="text-[13px] leading-[1.75] text-white/50 font-[family-name:var(--font-inter)]">
                        {item.a}
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}

          {/* CTA */}
          <div className="mt-4 p-5 bg-[#7c3aed]/5 border border-[#7c3aed]/12 rounded-xl flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <p className="text-[14px] text-white/50 flex-1 font-[family-name:var(--font-inter)]">
              Nenašli ste odpoveď?{' '}
              <strong className="text-[#c4b5fd]">Náš AI asistent</strong> odpovedá na ľubovoľné otázky — aj o polnoci.
            </p>
            <button
              onClick={() => document.getElementById('chat-trigger')?.click()}
              className="shrink-0 bg-[#7c3aed]/20 border border-[#7c3aed]/30 text-[#c4b5fd] px-4 py-2.5 rounded-lg text-[13px] font-bold"
            >
              🤖 Spýtať sa AI asistenta
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** za GallerySection
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add FAQSection with animated accordion"
```

---

## Task 16: Kontaktný formulár + Resend

**Files:**
- Create: `lib/contact.ts`
- Create: `__tests__/lib/contact.test.ts`
- Create: `components/sections/ContactSection.tsx`
- Modify: `.env.local` (manuálne — nie commitovať)

- [ ] **Nastav env** — vytvor `.env.local` (nie commitovať)

```bash
# .env.local
RESEND_API_KEY=re_xxxxxxxxxxxx
CONTACT_EMAIL=info@akhydroizol.sk
```

- [ ] **Pridaj `.env.local` do `.gitignore`**

```bash
echo ".env.local" >> .gitignore
```

- [ ] **Napíš test pre `lib/contact.ts`** — `__tests__/lib/contact.test.ts`

```ts
import { describe, it, expect } from 'vitest'
import { contactSchema } from '@/lib/contact'

describe('contactSchema', () => {
  it('validates correct data', () => {
    const result = contactSchema.safeParse({
      name: 'Ján Novák',
      phone: '+421900000000',
      address: 'Hlavná 1, Topoľčany',
      email: 'jan@email.sk',
      message: 'Mám vlhkú pivnicu.',
    })
    expect(result.success).toBe(true)
  })

  it('rejects missing name', () => {
    const result = contactSchema.safeParse({ phone: '+421900000000', address: 'x' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toContain('name')
  })

  it('rejects missing phone', () => {
    const result = contactSchema.safeParse({ name: 'Ján', address: 'x' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toContain('phone')
  })

  it('rejects missing address', () => {
    const result = contactSchema.safeParse({ name: 'Ján', phone: '+421900000000' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].path).toContain('address')
  })

  it('accepts empty optional fields', () => {
    const result = contactSchema.safeParse({
      name: 'Ján', phone: '+421900000000', address: 'x'
    })
    expect(result.success).toBe(true)
  })
})
```

- [ ] **Spusti — over FAIL**

```bash
npm run test:run -- __tests__/lib/contact.test.ts
```
Expected: FAIL — `Cannot find module '@/lib/contact'`

- [ ] **Vytvor `lib/contact.ts`**

```ts
'use server'
import { z } from 'zod'
import { Resend } from 'resend'

export const contactSchema = z.object({
  name: z.string().min(2, 'Meno je povinné'),
  phone: z.string().min(9, 'Telefón je povinný'),
  address: z.string().min(3, 'Adresa je povinná'),
  email: z.string().email('Neplatný email').optional().or(z.literal('')),
  message: z.string().optional(),
})

export type ContactFormData = z.infer<typeof contactSchema>

export async function sendContactEmail(data: ContactFormData): Promise<{ success: boolean; error?: string }> {
  const parsed = contactSchema.safeParse(data)
  if (!parsed.success) return { success: false, error: 'Neplatné dáta formulára' }

  const resend = new Resend(process.env.RESEND_API_KEY)
  const { name, phone, address, email, message } = parsed.data

  try {
    await resend.emails.send({
      from: 'web@akhydroizol.sk',
      to: process.env.CONTACT_EMAIL ?? 'info@akhydroizol.sk',
      subject: `Nová požiadavka o obhliadku — ${name}`,
      html: `
        <h2>Nová požiadavka o obhliadku</h2>
        <p><strong>Meno:</strong> ${name}</p>
        <p><strong>Telefón:</strong> ${phone}</p>
        <p><strong>Email:</strong> ${email || '—'}</p>
        <p><strong>Adresa:</strong> ${address}</p>
        <p><strong>Správa:</strong> ${message || '—'}</p>
      `,
    })
    return { success: true }
  } catch (e) {
    console.error('Resend error:', e)
    return { success: false, error: 'Odoslanie zlyhalo. Skúste zavolať priamo.' }
  }
}
```

- [ ] **Spusti — over PASS**

```bash
npm run test:run -- __tests__/lib/contact.test.ts
```
Expected: 5 passed

- [ ] **Vytvor `components/sections/ContactSection.tsx`**

```tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { contactSchema, type ContactFormData, sendContactEmail } from '@/lib/contact'

const TEL = '+421 900 000 000'
const REGIONS = ['Topoľčany', 'Partizánske', 'Bánovce n/B', 'Trenčín', 'Nitra']

export default function ContactSection() {
  const [status, setStatus] = useState<'idle' | 'sending' | 'ok' | 'err'>('idle')
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
  })

  const onSubmit = async (data: ContactFormData) => {
    setStatus('sending')
    const result = await sendContactEmail(data)
    if (result.success) { setStatus('ok'); reset() }
    else setStatus('err')
  }

  return (
    <section id="contact" className="py-20 px-8 bg-gradient-to-br from-[#0a0f1e] to-[#0f1a2e] relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-[#1A9AD6] to-[#F5A623]" />
      <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-16">

        {/* Kontaktné info */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-[#F5A623]" />
            <span className="text-[10px] font-bold text-[#F5A623] uppercase tracking-[2.5px] font-[family-name:var(--font-inter)]">Kontakt</span>
          </div>
          <h2 className="text-[36px] font-black tracking-[-1px] text-white mb-2">Začnite bezplatnou obhliadkou</h2>
          <p className="text-[14px] text-white/45 font-[family-name:var(--font-inter)] mb-8">Zavolajte, napíšte alebo vyplňte formulár — ozveme sa do 24 hodín</p>

          {/* Veľké tel. číslo */}
          <div className="flex items-center gap-4 p-5 bg-[#F5A623]/7 border border-[#F5A623]/20 rounded-2xl mb-6">
            <span className="text-3xl">📞</span>
            <div className="flex-1">
              <div className="text-[10px] text-white/35 font-[family-name:var(--font-inter)] mb-0.5">Zavolajte priamo</div>
              <a href={`tel:${TEL.replace(/\s/g, '')}`} className="text-[28px] font-black text-[#F5A623]">{TEL}</a>
            </div>
            <a href={`tel:${TEL.replace(/\s/g, '')}`}
              className="shrink-0 bg-[#F5A623] text-[#0d1626] px-4 py-2.5 rounded-xl text-[13px] font-black">
              Zavolať
            </a>
          </div>

          {/* Info */}
          {[
            { icon: '📧', title: 'info@akhydroizol.sk', sub: 'Odpovieme do 24 hodín' },
            { icon: '📍', title: 'Topoľčany / Partizánske', sub: 'Pôsobíme po celom regióne' },
            { icon: '🕐', title: 'Po–Pia: 7:00 – 18:00', sub: 'AI asistent dostupný 24/7' },
          ].map((item) => (
            <div key={item.title} className="flex items-center gap-3 mb-4 last:mb-0">
              <span className="text-[18px] w-9 text-center">{item.icon}</span>
              <div>
                <div className="text-[14px] font-bold text-white/85">{item.title}</div>
                <div className="text-[12px] text-white/40 font-[family-name:var(--font-inter)]">{item.sub}</div>
              </div>
            </div>
          ))}

          {/* Mapa regiónov — placeholder */}
          <div className="mt-6 bg-gradient-to-br from-[#0d1a2e] to-[#1a2d44] border border-[#1A9AD6]/20 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-[#1A9AD6]/10 text-[12px] font-bold text-[#1A9AD6] font-[family-name:var(--font-inter)]">
              📍 Oblasti pôsobenia
            </div>
            <div className="p-5 flex flex-wrap gap-2 justify-center">
              {REGIONS.map((r) => (
                <span key={r} className="px-3 py-1.5 bg-[#1A9AD6]/12 text-[#7dd3fc] text-[11px] rounded-full font-[family-name:var(--font-inter)]">{r}</span>
              ))}
            </div>
            <p className="text-center pb-4 text-[10px] text-white/15 font-[family-name:var(--font-inter)]">
              Nahradiť Google Maps embedom po spustení
            </p>
          </div>
        </div>

        {/* Formulár */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {status === 'ok' && (
            <div className="p-4 bg-[#16a34a]/15 border border-[#16a34a]/30 rounded-xl text-[14px] text-[#86efac] font-[family-name:var(--font-inter)]">
              ✅ Ďakujeme! Ozveme sa do 24 hodín.
            </div>
          )}
          {status === 'err' && (
            <div className="p-4 bg-[#dc2626]/15 border border-[#dc2626]/30 rounded-xl text-[14px] text-[#fca5a5] font-[family-name:var(--font-inter)]">
              ❌ Odoslanie zlyhalo. Zavolajte nám priamo.
            </div>
          )}

          {[
            { name: 'name' as const, label: 'Meno a priezvisko', placeholder: 'Ján Novák', required: true },
          ].map((f) => (
            <div key={f.name}>
              <label className="block text-[11px] font-bold text-white/40 uppercase tracking-widest mb-2 font-[family-name:var(--font-inter)]">{f.label}</label>
              <input {...register(f.name)} placeholder={f.placeholder}
                className="w-full bg-white/4 border border-white/8 rounded-xl px-4 py-3 text-[14px] text-white/60 placeholder:text-white/20 font-[family-name:var(--font-inter)] focus:outline-none focus:border-[#1A9AD6]/40" />
              {errors[f.name] && <p className="text-[12px] text-[#fca5a5] mt-1">{errors[f.name]?.message}</p>}
            </div>
          ))}

          <div className="grid grid-cols-2 gap-4">
            {[
              { name: 'phone' as const, label: 'Telefón *', placeholder: '+421 9XX XXX XXX' },
              { name: 'email' as const, label: 'E-mail (voliteľné)', placeholder: 'jan@email.sk' },
            ].map((f) => (
              <div key={f.name}>
                <label className="block text-[11px] font-bold text-white/40 uppercase tracking-widest mb-2 font-[family-name:var(--font-inter)]">{f.label}</label>
                <input {...register(f.name)} placeholder={f.placeholder}
                  className="w-full bg-white/4 border border-white/8 rounded-xl px-4 py-3 text-[14px] text-white/60 placeholder:text-white/20 font-[family-name:var(--font-inter)] focus:outline-none focus:border-[#1A9AD6]/40" />
                {errors[f.name] && <p className="text-[12px] text-[#fca5a5] mt-1">{errors[f.name]?.message}</p>}
              </div>
            ))}
          </div>

          <div>
            <label className="block text-[11px] font-bold text-white/40 uppercase tracking-widest mb-2 font-[family-name:var(--font-inter)]">Adresa nehnuteľnosti *</label>
            <input {...register('address')} placeholder="Ul. Novák 1, Topoľčany"
              className="w-full bg-white/4 border border-white/8 rounded-xl px-4 py-3 text-[14px] text-white/60 placeholder:text-white/20 font-[family-name:var(--font-inter)] focus:outline-none focus:border-[#1A9AD6]/40" />
            {errors.address && <p className="text-[12px] text-[#fca5a5] mt-1">{errors.address.message}</p>}
          </div>

          <div>
            <label className="block text-[11px] font-bold text-white/40 uppercase tracking-widest mb-2 font-[family-name:var(--font-inter)]">Opíšte problém</label>
            <textarea {...register('message')} placeholder="Vlhkosť v suteréne, mokré steny, plesne..." rows={3}
              className="w-full bg-white/4 border border-white/8 rounded-xl px-4 py-3 text-[14px] text-white/60 placeholder:text-white/20 font-[family-name:var(--font-inter)] resize-none focus:outline-none focus:border-[#1A9AD6]/40" />
          </div>

          <button type="submit" disabled={status === 'sending'}
            className="w-full bg-[#1A9AD6] text-white py-4 rounded-xl text-[15px] font-bold disabled:opacity-60 transition-opacity">
            {status === 'sending' ? 'Odosielam...' : 'Odoslať požiadavku o obhliadku →'}
          </button>

          <p className="text-[11px] text-white/20 text-center font-[family-name:var(--font-inter)]">
            Odoslaním súhlasíte so spracovaním osobných údajov. Vaše dáta nikdy nepredávame.
          </p>
        </form>
      </div>
    </section>
  )
}
```

- [ ] **Pridaj do `app/page.tsx`** za FAQSection
- [ ] **Over formulár** — `npm run dev`, vyplň formulár, over Resend dashboard (alebo Mailtrap počas vývoja)
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add ContactSection with RHF + Zod + Resend server action"
```

---

## Task 17: Galéria s lightboxom (po dodaní fotiek)

> **Poznámka:** Tento task sa dokončí keď klient dodá fotky. Placeholder je hotový v Task 13.

**Files:**
- Modify: `components/sections/GallerySection.tsx`

- [ ] **Keď klient dodá fotky** — umiestni ich do `public/gallery/` a aktualizuj GallerySection:

```tsx
'use client'
import PhotoAlbum from 'react-photo-album'
import Lightbox from 'yet-another-react-lightbox'
import 'yet-another-react-lightbox/styles.css'
import { useState } from 'react'

// Nahradiť reálnymi fotkami
const PHOTOS = [
  { src: '/gallery/01.jpg', width: 800, height: 600, alt: 'Podrezávanie Topoľčany — výsledok' },
  { src: '/gallery/02.jpg', width: 600, height: 800, alt: 'Hydroizolácia základov Partizánske' },
  // ... ďalšie fotky
]

export default function GallerySection() {
  const [index, setIndex] = useState(-1)
  return (
    <section id="gallery" className="py-20 px-8 bg-[#060a14]">
      <div className="max-w-6xl mx-auto">
        {/* header rovnaký ako v placeholder verzii */}
        <PhotoAlbum
          layout="masonry"
          photos={PHOTOS}
          onClick={({ index }) => setIndex(index)}
          columns={(w) => (w < 640 ? 2 : w < 1024 ? 3 : 4)}
        />
        <Lightbox open={index >= 0} close={() => setIndex(-1)} index={index} slides={PHOTOS} />
      </div>
    </section>
  )
}
```

- [ ] **Commit po dodaní fotiek**

```bash
git add public/gallery/ components/sections/GallerySection.tsx
git commit -m "feat: add real gallery photos with lightbox"
```
