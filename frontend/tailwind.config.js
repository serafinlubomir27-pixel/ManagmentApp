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
      borderRadius: {
        control: '0.5rem',   //  8px — tlačidlá, vstupy, drobné štítky
        card:    '0.875rem', // 14px — karty, panely
        modal:   '1.25rem',  // 20px — modály, veľké plochy
      },

      // Výška nad plochou. V tmavom režime tieň nevidno, preto sa tam opiera
      // o jemný svetlý okraj — to rieši `.card` a spol. v index.css.
      boxShadow: {
        card:    '0 1px 2px 0 rgb(22 28 43 / 0.04), 0 1px 3px 0 rgb(22 28 43 / 0.06)',
        raised:  '0 4px 12px -2px rgb(22 28 43 / 0.08), 0 2px 6px -2px rgb(22 28 43 / 0.06)',
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
      fontSize: {
        display: ['clamp(2.25rem, 1.5rem + 2.6vw, 3.5rem)', { lineHeight: '1.08', letterSpacing: '-0.025em' }],
        title:   ['clamp(1.65rem, 1.3rem + 1.1vw, 2.25rem)', { lineHeight: '1.15', letterSpacing: '-0.02em' }],
      },

      keyframes: {
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'none' },
        },
      },
      animation: {
        'fade-up': 'fade-up 280ms cubic-bezier(0.22, 1, 0.36, 1) both',
      },
    },
  },
  plugins: [],
}
