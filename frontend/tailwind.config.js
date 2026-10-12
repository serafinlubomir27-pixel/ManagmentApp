/** @type {import('tailwindcss').Config} */

// Dizajnové tokeny.
//
// Monday.com má verejný systém Vibe a jeho sila nie je vo farbách — je v tom, že
// každý odstup, rádius aj tieň siaha po tej istej pomenovanej hodnote. Nič nevyzerá
// „skoro rovnako". Doteraz tu boli tokeny len na farby a zvyšok sa dopisoval od oka
// (rounded-lg vedľa rounded-xl vedľa rounded-2xl, p-5 vedľa p-6 vedľa p-7).
//
// Sivé odtiene sú zámerne mierne tónované do modrej. Čisto neutrálna sivá vedľa
// modrej značky pôsobí špinavo; spoločný nádych je dôvod, prečo paleta drží spolu.

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef3ff',
          100: '#dde7ff',
          200: '#c2d4ff',
          300: '#9bb6ff',
          400: '#7194ff',
          500: '#4B7FFF',
          600: '#3b6ee8',
          700: '#2d5ed0',
          800: '#2449a3',
          900: '#1e3a7d',
        },
        // Neutrály s modrým nádychom — ladia so značkou namiesto toho, aby s ňou bojovali.
        ink: {
          50:  '#f6f8fc',
          100: '#eef1f8',
          200: '#dfe4ef',
          300: '#c5cddd',
          400: '#98a3b8',
          500: '#6c7891',
          600: '#4e5970',
          700: '#3a4257',
          800: '#242b3d',
          900: '#161c2b',
        },
        // Appka má `gray-*` na vyše 900 miestach. Prepísať ich po jednom by bola
        // zbytočná zmena v štyridsiatich súboroch — stačí presmerovať `gray` na
        // ladené neutrály a vzhľad sa zjednotí naraz.
        gray: {
          50:  '#f6f8fc',
          100: '#eef1f8',
          200: '#dfe4ef',
          300: '#c5cddd',
          400: '#98a3b8',
          500: '#6c7891',
          600: '#4e5970',
          700: '#3a4257',
          800: '#242b3d',
          900: '#161c2b',
        },
        surface: {
          DEFAULT: '#ffffff',
          dark: '#101629',
          // O stupeň vyššie než plocha — dropdowny, modály, vnorené karty.
          raised: '#ffffff',
          'raised-dark': '#171f36',
        },
        bg: {
          DEFAULT: '#F5F7FF',
          dark: '#0A0E1A',
        },
      },

      // Rádiusy podľa úlohy prvku, nie podľa čísla v pixeloch.
      // Hodnoty kariet a pilulky vychádzajú z merania monday.com (karty 20 px,
      // tlačidlá plne zaoblené) — nie z odhadu.
      borderRadius: {
        control: '0.5rem',   //  8px — vstupy a tlačidlá v aplikácii
        card:    '1.25rem',  // 20px — karty a panely
        modal:   '1.5rem',   // 24px — modály, veľké plochy
        pill:    '9999px',   //       — výzvy na marketingovej stránke
      },

      // Výška nad plochou. V tmavom režime tieň nevidno, preto sa tam opiera
      // o jemný svetlý okraj — to rieši `.card` a spol. v index.css.
      // Monday používa jeden mäkký rozptýlený tieň (0 4px 20px rgba(0,0,0,.1))
      // namiesto dvoch tvrdších vrstiev. Preto sú tiene väčšie a rozostrenejšie
      // než pôvodné — plocha tým pôsobí, že sa vznáša, nie že je orámovaná.
      boxShadow: {
        card:    '0 2px 10px -2px rgb(22 28 43 / 0.07)',
        raised:  '0 4px 20px 0 rgb(22 28 43 / 0.10)',
        float:   '0 18px 48px -12px rgb(22 28 43 / 0.22)',
        overlay: '0 16px 40px -8px rgb(22 28 43 / 0.18), 0 4px 12px -4px rgb(22 28 43 / 0.1)',
        glow:    '0 0 0 4px rgb(75 127 255 / 0.12)',
      },

      transitionDuration: {
        fast: '120ms',   // zmena stavu pod kurzorom
        base: '180ms',   // bežný prechod
        slow: '280ms',   // vstup plochy, rozbalenie
      },
      transitionTimingFunction: {
        // Rýchly nástup, mäkké dobehnutie — pohyb pôsobí odpovedavo, nie lenivo.
        out: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },

      // Nadpisy potrebujú tesnejšie riadkovanie a záporné prestrkanie, inak pri
      // veľkých stupňoch pôsobia rozdrobene.
      // Nadpisy na monday.com majú hrúbku 400 a prestrkanie −0,03 em. Pri Inter
      // by 400 pôsobilo chudokrvne — Poppins má podstatne sýtejší základný rez.
      // Zodpovedajúcim prekladom je 600; princíp (veľký stupeň, tesné
      // prestrkanie, ľahší rez než by človek čakal) ostáva zachovaný.
      fontSize: {
        display: ['clamp(2.5rem, 1.5rem + 3.2vw, 4.5rem)', { lineHeight: '1.02', letterSpacing: '-0.032em' }],
        title:   ['clamp(1.75rem, 1.3rem + 1.6vw, 3rem)',  { lineHeight: '1.08', letterSpacing: '-0.028em' }],
        lead:    ['1.25rem', { lineHeight: '1.6' }],
      },

      keyframes: {
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'none' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        // Modály a rozbaľovacie ponuky — mierne priblíženie pôsobí, akoby
        // vyrástli z miesta, nie akoby na obsah spadli.
        'pop-in': {
          from: { opacity: '0', transform: 'scale(0.97) translateY(6px)' },
          to:   { opacity: '1', transform: 'none' },
        },
        // Pulz pre hodnoty, ktoré sa práve prepočítali.
        'flash': {
          '0%':   { backgroundColor: 'rgb(75 127 255 / 0.18)' },
          '100%': { backgroundColor: 'transparent' },
        },
      },
      animation: {
        'fade-up': 'fade-up 280ms cubic-bezier(0.22, 1, 0.36, 1) both',
        'fade-in': 'fade-in 180ms ease-out both',
        'pop-in':  'pop-in 180ms cubic-bezier(0.22, 1, 0.36, 1) both',
        'flash':   'flash 900ms ease-out',
      },
    },
  },
  plugins: [],
}
