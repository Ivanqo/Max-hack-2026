/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: 'rgb(var(--brand-50) / <alpha-value>)',
          100: 'rgb(var(--brand-100) / <alpha-value>)',
          200: 'rgb(var(--brand-200) / <alpha-value>)',
          300: 'rgb(var(--brand-300) / <alpha-value>)',
          400: 'rgb(var(--brand-400) / <alpha-value>)',
          500: 'rgb(var(--brand-500) / <alpha-value>)',
          600: 'rgb(var(--brand-600) / <alpha-value>)',
          700: 'rgb(var(--brand-700) / <alpha-value>)',
          800: 'rgb(var(--brand-800) / <alpha-value>)',
          900: 'rgb(var(--brand-900) / <alpha-value>)',
          950: 'rgb(var(--brand-950) / <alpha-value>)',
        },
        accent: {
          50: 'rgb(var(--accent-50) / <alpha-value>)',
          100: 'rgb(var(--accent-100) / <alpha-value>)',
          200: 'rgb(var(--accent-200) / <alpha-value>)',
          300: 'rgb(var(--accent-300) / <alpha-value>)',
          400: 'rgb(var(--accent-400) / <alpha-value>)',
          500: 'rgb(var(--accent-500) / <alpha-value>)',
          600: 'rgb(var(--accent-600) / <alpha-value>)',
          700: 'rgb(var(--accent-700) / <alpha-value>)',
          800: 'rgb(var(--accent-800) / <alpha-value>)',
          900: 'rgb(var(--accent-900) / <alpha-value>)',
          950: 'rgb(var(--accent-950) / <alpha-value>)',
        },
        ink: {
          50: '#f6f6f9',
          100: '#ececf2',
          200: '#d7d7e3',
          300: '#b3b3c6',
          400: '#8a8aa3',
          500: '#6c6c88',
          600: '#56566f',
          700: '#46465b',
          800: '#3b3b4c',
          900: '#252531',
          950: '#17171f',
        },
      },
      boxShadow: {
        soft: '0 1px 2px 0 rgb(23 23 31 / 0.04), 0 1px 3px 0 rgb(23 23 31 / 0.06)',
        card: '0 2px 6px -1px rgb(23 23 31 / 0.06), 0 8px 24px -8px rgb(23 23 31 / 0.10)',
        pop: '0 12px 32px -8px rgb(var(--brand-600) / 0.28)',
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, rgb(var(--brand-700)) 0%, rgb(var(--brand-500)) 55%, rgb(var(--accent-400)) 130%)',
        'brand-gradient-soft': 'linear-gradient(135deg, rgb(var(--brand-50)) 0%, rgb(var(--accent-50)) 100%)',
      },
      animation: {
        'fade-in': 'fade-in .35s ease-out',
        'slide-up': 'slide-up .35s cubic-bezier(0.16,1,0.3,1)',
        'scale-in': 'scale-in .2s cubic-bezier(0.16,1,0.3,1)',
      },
      keyframes: {
        'fade-in': { from: { opacity: 0 }, to: { opacity: 1 } },
        'slide-up': { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        'scale-in': { from: { opacity: 0, transform: 'scale(.96)' }, to: { opacity: 1, transform: 'scale(1)' } },
      },
    },
  },
  plugins: [],
}
