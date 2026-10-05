/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#04070D',
          900: '#060A14', // Base background
          850: '#090E1B',
          800: '#0D1527', // Card surface
          750: '#101A30', // Elevated surface
          700: '#15223E', // Popover / modal
        },
        sovereign: {
          amber: '#F2B84B',
          'amber-glow': 'rgba(242, 184, 75, 0.25)',
          'amber-hover': '#F5C46B',
          ice: '#38BDF8',
          'ice-glow': 'rgba(56, 189, 248, 0.2)',
          emerald: '#10B981',
          rose: '#EF4444',
          violet: '#818CF8',
        },
        border: {
          subtle: '#17233B',
          DEFAULT: '#1E2D4A',
          active: '#2E446E',
          glow: '#F2B84B40',
        },
      },
      fontFamily: {
        display: ['Sora', 'sans-serif'],
        sans: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'receipt': '0 0 0 1px #1E2D4A, 0 8px 32px rgba(6, 10, 20, 0.8), 0 0 24px rgba(242, 184, 75, 0.08)',
        'amber-glow': '0 0 20px rgba(242, 184, 75, 0.25)',
        'ice-glow': '0 0 20px rgba(56, 189, 248, 0.2)',
        'emerald-glow': '0 0 20px rgba(16, 185, 129, 0.25)',
        'rose-glow': '0 0 20px rgba(239, 68, 68, 0.25)',
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-up': 'slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
