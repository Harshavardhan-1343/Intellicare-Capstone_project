/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        'inter': ['Inter', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#e6f2ff',
          100: '#cce5ff',
          500: '#007bff',
          600: '#0056b3',
          700: '#004085',
        },
        success: '#34d399',
        warning: '#fbbf24',
        danger: '#ef4444',
        emergency: '#dc2626',
        urgent: '#f97316',
        semiUrgent: '#eab308',
        nonUrgent: '#22c55e',
        deceased: '#374151',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'rotate-slow': 'rotate 20s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        }
      }
    },
  },
  plugins: [],
};