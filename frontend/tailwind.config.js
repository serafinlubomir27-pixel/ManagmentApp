/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          500: '#4B7FFF',
          600: '#3b6ee8',
          700: '#2d5ed0',
        },
        surface: {
          DEFAULT: '#ffffff',
          dark: '#101629',
        },
        bg: {
          DEFAULT: '#F5F7FF',
          dark: '#0A0E1A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
