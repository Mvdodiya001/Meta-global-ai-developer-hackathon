/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ct: {
          accent: 'rgb(var(--ct-accent) / <alpha-value>)',
          surface: 'rgb(var(--ct-surface) / <alpha-value>)',
        },
      },
      fontFamily: {
        sans: [
          'IBM Plex Sans',
          'Segoe UI',
          'system-ui',
          'sans-serif',
        ],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
