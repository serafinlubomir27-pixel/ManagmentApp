# akhydroizol.sk — Fáza 4: SEO (JSON-LD) + AI Chatbot

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementovať JSON-LD structured data (LocalBusiness, FAQPage, HowTo, Service) a AI chatbot widget napojený na Claude API so streamingom.

**Architecture:** JSON-LD generátory sú čisté funkcie v `lib/jsonld.ts` — vkladajú sa do `<head>` cez `app/layout.tsx`. Chatbot: Next.js Route Handler (`/api/chat`) so streamingom, `useChat` hook riadi stav, `ChatWidget` je floating bubble.

**Tech Stack:** @anthropic-ai/sdk, Vercel AI SDK streaming, Framer Motion (chatbot panel)

**Prerekvizita:** Fáza 1–3 dokončená.

---

## Task 18: JSON-LD Structured Data

**Files:**
- Create: `lib/jsonld.ts`
- Create: `__tests__/lib/jsonld.test.ts`
- Modify: `app/layout.tsx`

- [ ] **Napíš testy** — `__tests__/lib/jsonld.test.ts`

```ts
import { describe, it, expect } from 'vitest'
import { buildLocalBusiness, buildFAQPage, buildHowTo, buildService } from '@/lib/jsonld'

describe('buildLocalBusiness', () => {
  it('returns correct @type', () => {
    const schema = buildLocalBusiness()
    expect(schema['@type']).toBe('LocalBusiness')
  })
  it('includes telephone', () => {
    const schema = buildLocalBusiness()
    expect(schema.telephone).toBeDefined()
  })
  it('includes areaServed with 5 regions', () => {
    const schema = buildLocalBusiness()
    expect(schema.areaServed).toHaveLength(5)
  })
})

describe('buildFAQPage', () => {
  const faqs = [{ q: 'Otázka?', a: 'Odpoveď.' }]
  it('returns FAQPage type', () => {
    expect(buildFAQPage(faqs)['@type']).toBe('FAQPage')
  })
  it('maps questions to mainEntity', () => {
    const schema = buildFAQPage(faqs)
    expect(schema.mainEntity[0].name).toBe('Otázka?')
    expect(schema.mainEntity[0].acceptedAnswer.text).toBe('Odpoveď.')
  })
})

describe('buildHowTo', () => {
  it('returns HowTo type', () => {
    expect(buildHowTo()['@type']).toBe('HowTo')
  })
  it('has 4 steps', () => {
    expect(buildHowTo().step).toHaveLength(4)
  })
})

describe('buildService', () => {
  it('returns Service type', () => {
    expect(buildService()['@type']).toBe('Service')
  })
  it('includes provider reference', () => {
    expect(buildService().provider).toBeDefined()
  })
})
```

- [ ] **Spusti — over FAIL**

```bash
npm run test:run -- __tests__/lib/jsonld.test.ts
```

- [ ] **Vytvor `lib/jsonld.ts`**

```ts
const BUSINESS_NAME = 'AK Hydroizol'
const TELEPHONE = '+421900000000'
const URL = 'https://akhydroizol.sk'
const REGIONS = ['Topoľčany', 'Partizánske', 'Bánovce nad Bebravou', 'Trenčín', 'Nitra']

export function buildLocalBusiness() {
  return {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: BUSINESS_NAME,
    url: URL,
    telephone: TELEPHONE,
    email: 'info@akhydroizol.sk',
    description: 'Podrezávanie domov a hydroizolácia základov existujúcich stavieb. 20 rokov skúseností, 10-ročná záruka.',
    address: {
      '@type': 'PostalAddress',
      addressLocality: 'Topoľčany',
      addressRegion: 'Nitra',
      addressCountry: 'SK',
    },
    areaServed: REGIONS.map((r) => ({ '@type': 'City', name: r })),
    openingHoursSpecification: [
      {
        '@type': 'OpeningHoursSpecification',
        dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        opens: '07:00',
        closes: '18:00',
      },
    ],
    priceRange: '€€',
  }
}

export function buildFAQPage(faqs: Array<{ q: string; a: string }>) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.q,
      acceptedAnswer: { '@type': 'Answer', text: faq.a },
    })),
  }
}

export function buildHowTo() {
  return {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: 'Ako prebieha podrezávanie domu',
    description: 'Proces podrezávania domu od konzultácie po odovzdanie s 10-ročnou zárukou.',
    totalTime: 'P3D',
    step: [
      {
        '@type': 'HowToStep',
        position: 1,
        name: 'Bezplatná konzultácia',
        text: 'Kontaktujte nás telefonicky alebo cez formulár. Do 24 hodín dohodneme obhliadku.',
      },
      {
        '@type': 'HowToStep',
        position: 2,
        name: 'Obhliadka a meranie',
        text: 'Technická obhliadka na mieste, meranie rozsahu vlhkosti, cenová ponuka.',
      },
      {
        '@type': 'HowToStep',
        position: 3,
        name: 'Realizácia podrezávania',
        text: 'Diamantovým lanom prerežeme murivo a vložíme hydroizolačnú fóliu. Trvá 1–3 dni.',
      },
      {
        '@type': 'HowToStep',
        position: 4,
        name: 'Odovzdanie s 10-ročnou zárukou',
        text: 'Prácu odovzdáme s písomnou zárukou na 10 rokov.',
      },
    ],
  }
}

export function buildService() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: 'Podrezávanie domov a hydroizolácia základov',
    description: 'Mechanická metóda dodatočnej hydroizolácie existujúcich stavieb pomocou diamantového lana.',
    provider: { '@type': 'LocalBusiness', name: BUSINESS_NAME, url: URL },
    areaServed: REGIONS.map((r) => ({ '@type': 'City', name: r })),
    hasOfferCatalog: {
      '@type': 'OfferCatalog',
      name: 'Hydroizolačné služby',
      itemListElement: [
        { '@type': 'Offer', itemOffered: { '@type': 'Service', name: 'Podrezávanie domu' } },
        { '@type': 'Offer', itemOffered: { '@type': 'Service', name: 'Hydroizolácia pivnice' } },
        { '@type': 'Offer', itemOffered: { '@type': 'Service', name: 'Sanácia vlhkých stien' } },
      ],
    },
  }
}
```

- [ ] **Spusti — over PASS**

```bash
npm run test:run -- __tests__/lib/jsonld.test.ts
```
Expected: 8 passed

- [ ] **Vlož JSON-LD do `app/layout.tsx`**

```tsx
// Pridaj import na vrch
import { buildLocalBusiness, buildHowTo, buildService } from '@/lib/jsonld'

// V <head> sekcii layoutu (pred </head>):
// Next.js 15 App Router — pridáš do <head> cez generateMetadata alebo priamo:
export default function RootLayout({ children }: { children: React.ReactNode }) {
  const schemas = [buildLocalBusiness(), buildHowTo(), buildService()]

  return (
    <html lang="sk" className={`${dmSans.variable} ${inter.variable}`}>
      <head>
        {schemas.map((schema, i) => (
          <script
            key={i}
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
          />
        ))}
      </head>
      <body>{children}</body>
    </html>
  )
}
```

- [ ] **FAQPage JSON-LD** — vlož do `components/sections/FAQSection.tsx`

```tsx
// Na vrch súboru:
import { buildFAQPage } from '@/lib/jsonld'

// FAQ_ITEMS je už definovaný — pridaj schema na začiatok returnu:
const faqSchema = buildFAQPage(FAQ_ITEMS.map((f) => ({ q: f.q, a: f.a })))

// Do JSX pred <section>:
<>
  <script
    type="application/ld+json"
    dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
  />
  <section id="faq" ...>
    {/* existujúci obsah */}
  </section>
</>
```

- [ ] **Over** — `npm run dev` → DevTools → Elements → hľadaj `<script type="application/ld+json">`
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add JSON-LD schemas (LocalBusiness, FAQPage, HowTo, Service)"
```

---

## Task 19: Claude API Route Handler

**Files:**
- Create: `app/api/chat/route.ts`
- Modify: `.env.local`

- [ ] **Pridaj API key do `.env.local`**

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
```

- [ ] **Vytvor `app/api/chat/route.ts`**

```ts
import Anthropic from '@anthropic-ai/sdk'
import { NextRequest } from 'next/server'

const client = new Anthropic()

const SYSTEM_PROMPT = `Si AI asistent firmy AK Hydroizol. Odpovedáš na otázky zákazníkov o podrezávaní domov a hydroizolácii základov.

FAKTY O FIRME:
- AK Hydroizol, Topoľčany/Partizánske, Slovensko
- 20 rokov skúseností (od 2004), 500+ zrealizovaných domov
- 10-ročná písomná záruka na každú realizáciu
- Bezplatná obhliadka do 24 hodín
- Telefón: +421 900 000 000
- Regióny: Topoľčany, Partizánske, Bánovce n/B, Trenčín, Nitra
- Ceny: od 2 000 do 5 000 € pre bežný dom (závisí od muriva)
- Trvanie prác: 1–3 dni

SPRÁVANIE:
- Odpovedaj stručne a konkrétne, v slovenčine
- Ak sa pýtajú na cenu, daj orientačné čísla a povedz aby zavolali na obhliadku
- Ak nevieš odpovedať, navrhni zavolať: +421 900 000 000
- Nepriznávaj žiadne nevýhody oproti konkurencii
- Max 3–4 vety na odpoveď`

export async function POST(req: NextRequest) {
  const { messages } = await req.json()

  const stream = await client.messages.stream({
    model: 'claude-haiku-4-5',
    max_tokens: 400,
    system: SYSTEM_PROMPT,
    messages: messages.map((m: { role: string; content: string }) => ({
      role: m.role,
      content: m.content,
    })),
  })

  const encoder = new TextEncoder()

  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        if (
          chunk.type === 'content_block_delta' &&
          chunk.delta.type === 'text_delta'
        ) {
          controller.enqueue(encoder.encode(chunk.delta.text))
        }
      }
      controller.close()
    },
  })

  return new Response(readable, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  })
}
```

- [ ] **Over API route manuálne**

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Koľko stojí podrezávanie?"}]}'
```
Expected: streaming text odpoveď

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add Claude API streaming route handler"
```

---

## Task 20: useChat hook

**Files:**
- Create: `hooks/useChat.ts`
- Create: `__tests__/hooks/useChat.test.ts`

- [ ] **Napíš test** — `__tests__/hooks/useChat.test.ts`

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useChat } from '@/hooks/useChat'

// Mock fetch
global.fetch = vi.fn()

describe('useChat', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('starts with empty messages', () => {
    const { result } = renderHook(() => useChat())
    expect(result.current.messages).toHaveLength(0)
  })

  it('adds user message on send', async () => {
    ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      body: new ReadableStream({ start(c) { c.close() } }),
    })
    const { result } = renderHook(() => useChat())
    await act(async () => { await result.current.send('Testová otázka') })
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.messages[0].content).toBe('Testová otázka')
  })

  it('sets loading true during request', async () => {
    let resolve: () => void
    const pending = new Promise<void>((r) => { resolve = r })
    ;(global.fetch as ReturnType<typeof vi.fn>).mockReturnValue(
      pending.then(() => ({ ok: true, body: new ReadableStream({ start(c) { c.close() } }) }))
    )
    const { result } = renderHook(() => useChat())
    act(() => { result.current.send('Test') })
    expect(result.current.loading).toBe(true)
    resolve!()
  })
})
```

- [ ] **Spusti — over FAIL**

```bash
npm run test:run -- __tests__/hooks/useChat.test.ts
```

- [ ] **Vytvor `hooks/useChat.ts`**

```ts
import { useState, useCallback } from 'react'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)

  const send = useCallback(async (text: string) => {
    if (!text.trim() || loading) return
    const userMsg: Message = { role: 'user', content: text.trim() }
    const nextMessages = [...messages, userMsg]
    setMessages(nextMessages)
    setLoading(true)

    const assistantMsg: Message = { role: 'assistant', content: '' }
    setMessages([...nextMessages, assistantMsg])

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages }),
      })
      if (!res.ok || !res.body) throw new Error('API error')

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let full = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        full += decoder.decode(value, { stream: true })
        setMessages([...nextMessages, { role: 'assistant', content: full }])
      }
    } catch {
      setMessages([...nextMessages, { role: 'assistant', content: 'Prepáčte, nastala chyba. Zavolajte nám: +421 900 000 000' }])
    } finally {
      setLoading(false)
    }
  }, [messages, loading])

  const clear = useCallback(() => setMessages([]), [])

  return { messages, loading, send, clear }
}
```

- [ ] **Spusti — over PASS**

```bash
npm run test:run -- __tests__/hooks/useChat.test.ts
```
Expected: 3 passed

- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add useChat hook with streaming (tested)"
```

---

## Task 21: ChatWidget UI

**Files:**
- Create: `components/chatbot/ChatMessage.tsx`
- Create: `components/chatbot/ChatPanel.tsx`
- Create: `components/chatbot/ChatWidget.tsx`
- Modify: `app/page.tsx`

- [ ] **Vytvor `components/chatbot/ChatMessage.tsx`**

```tsx
import type { Message } from '@/hooks/useChat'

export default function ChatMessage({ msg }: { msg: Message }) {
  const isBot = msg.role === 'assistant'
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      <div className={`max-w-[85%] px-3.5 py-2.5 rounded-xl text-[13px] leading-relaxed font-[family-name:var(--font-inter)] ${
        isBot
          ? 'bg-white/6 text-white/80 rounded-tl-sm'
          : 'bg-gradient-to-br from-[#7c3aed] to-[#5b21b6] text-white rounded-tr-sm'
      }`}>
        {msg.content || <span className="opacity-40 animate-pulse">●●●</span>}
      </div>
    </div>
  )
}
```

- [ ] **Vytvor `components/chatbot/ChatPanel.tsx`**

```tsx
'use client'
import { useRef, useEffect, useState, KeyboardEvent } from 'react'
import { useChat } from '@/hooks/useChat'
import ChatMessage from './ChatMessage'

const WELCOME: import('@/hooks/useChat').Message = {
  role: 'assistant',
  content: 'Dobrý deň! Som AI asistent AK Hydroizol. Môžem vám pomôcť s otázkami o podrezávaní, cenách alebo obhliadke. Čo vás zaujíma?',
}

export default function ChatPanel({ onClose }: { onClose: () => void }) {
  const { messages, loading, send } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const allMessages = [WELCOME, ...messages]

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [allMessages.length])

  const handleSend = () => { send(input); setInput('') }
  const onKey = (e: KeyboardEvent) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#7c3aed] to-[#5b21b6] px-4 py-4 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-lg">🤖</div>
        <div className="flex-1">
          <div className="text-[14px] font-bold text-white">AK Hydroizol AI Asistent</div>
          <div className="text-[11px] text-white/60 font-[family-name:var(--font-inter)]">Powered by Claude · Online 24/7</div>
        </div>
        <div className="w-2 h-2 rounded-full bg-[#4ade80] shadow-[0_0_6px_#4ade80]" />
        <button onClick={onClose} className="text-white/60 hover:text-white ml-2 text-lg">✕</button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {allMessages.map((msg, i) => <ChatMessage key={i} msg={msg} />)}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-white/6 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Napíšte otázku..."
          className="flex-1 bg-white/5 border border-white/8 rounded-lg px-3 py-2.5 text-[13px] text-white/70 placeholder:text-white/25 font-[family-name:var(--font-inter)] focus:outline-none focus:border-[#7c3aed]/50"
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}
          className="w-9 h-9 bg-[#7c3aed] rounded-lg flex items-center justify-center text-white disabled:opacity-40 shrink-0">
          ➤
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Vytvor `components/chatbot/ChatWidget.tsx`**

```tsx
'use client'
import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import ChatPanel from './ChatPanel'

export default function ChatWidget() {
  const [open, setOpen] = useState(false)

  return (
    <div className="fixed bottom-20 right-4 md:bottom-6 md:right-6 z-50">
      <AnimatePresence>
        {open && (
          <motion.div
            key="panel"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-16 right-0 w-[340px] h-[480px] bg-[#0d1626] border border-[#7c3aed]/20 rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col"
          >
            <ChatPanel onClose={() => setOpen(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating bubble */}
      <button
        id="chat-trigger"
        onClick={() => setOpen(!open)}
        className="w-14 h-14 bg-[#7c3aed] rounded-full flex items-center justify-center text-2xl shadow-[0_4px_20px_rgba(124,58,237,0.5)] hover:scale-105 transition-transform"
        aria-label="Otvoriť AI asistenta"
      >
        {open ? '✕' : '🤖'}
      </button>
    </div>
  )
}
```

- [ ] **Pridaj ChatWidget do `app/page.tsx`** za `<MobileStickyBar />`

```tsx
import ChatWidget from '@/components/chatbot/ChatWidget'

// v returne:
<ChatWidget />
```

- [ ] **Over** — `npm run dev` → floating fialová bublina vpravo dole → klik → chat panel sa otvorí → napíš otázku → streaming odpoveď
- [ ] **Commit**

```bash
git add -A && git commit -m "feat: add AI chatbot widget with Claude streaming"
```
