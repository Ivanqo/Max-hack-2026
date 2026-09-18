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
          50: '#f1f0ff',
          100: '#e4e1fe',
          200: '#cbc5fd',
          300: '#aa9ffb',
          400: '#8b76f7',
          500: '#7150f0',
          600: '#6238e0',
          700: '#5229c4',
          800: '#43229f',
          900: '#391f7f',
          950: '#221254',
        },
        accent: {
          50: '#eafff7',
          100: '#ccfeeb',
          200: '#9bfcda',
          300: '#5df3c4',
          400: '#26e0ac',
          500: '#0cc796',
          600: '#04a17b',
          700: '#067f65',
          800: '#0a6552',
          900: '#0b5344',
          950: '#012f27',
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
        pop: '0 12px 32px -8px rgb(98 56 224 / 0.28)',
      },
      borderRadius: {
        xl: '0.875rem',
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #6238e0 0%, #7150f0 55%, #26e0ac 130%)',
        'brand-gradient-soft': 'linear-gradient(135deg, #f1f0ff 0%, #eafff7 100%)',
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
