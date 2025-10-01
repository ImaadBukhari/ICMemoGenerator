/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#a6ddce', // Main highlight color
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
        cyber: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        dark: {
          50: '#18181b',
          100: '#27272a',
          200: '#3f3f46',
          300: '#52525b',
          400: '#71717a',
          500: '#a1a1aa',
          600: '#d4d4d8',
          700: '#e4e4e7',
          800: '#f4f4f5',
          900: '#fafafa',
        }
      },
      fontFamily: {
        'mono': ['JetBrains Mono', 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'monospace'],
        'tech': ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-in',
        'cyber-flicker': 'cyber-flicker 3s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': {
            opacity: 1,
            boxShadow: '0 0 5px #a6ddce, 0 0 10px #a6ddce, 0 0 15px #a6ddce',
          },
          '50%': {
            opacity: 0.7,
            boxShadow: '0 0 10px #a6ddce, 0 0 20px #a6ddce, 0 0 30px #a6ddce',
          },
        },
        'slide-up': {
          '0%': {
            opacity: 0,
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateY(0)',
          },
        },
        'fade-in': {
          '0%': {
            opacity: 0,
          },
          '100%': {
            opacity: 1,
          },
        },
        'cyber-flicker': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.8 },
          '75%': { opacity: 0.9 },
        },
      },
      boxShadow: {
        'cyber': '0 0 10px rgba(166, 221, 206, 0.3), 0 4px 20px rgba(0, 0, 0, 0.3)',
        'cyber-lg': '0 0 20px rgba(166, 221, 206, 0.4), 0 8px 30px rgba(0, 0, 0, 0.4)',
        'inner-cyber': 'inset 0 0 10px rgba(166, 221, 206, 0.2)',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}