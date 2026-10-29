/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg: '#F8FAF8',
          surface: '#FFFFFF',
          primary: '#1B4D3E',
          'primary-hover': '#153E32',
          secondary: '#E7F1EB',
          soft: '#F0F6F1',
          text: '#202824',
          muted: '#66736C',
          border: '#E3E9E4',
          warning: '#B7791F',
          error: '#C2413B',
          success: '#27815B',
        },
        ivory: {
          DEFAULT: '#F8FAF8',
          50: '#FCFDFC',
          100: '#F8FAF8',
          200: '#F0F6F1',
          300: '#E7F1EB',
          card: '#FFFFFF',
          surface: '#FFFFFF',
        },
        forest: {
          DEFAULT: '#1B4D3E',
          50: '#F0F6F1',
          100: '#E7F1EB',
          200: '#C5DCCF',
          300: '#95C1AA',
          400: '#5A9F7E',
          500: '#2D7A58',
          600: '#1B4D3E', // Core Primary
          700: '#153E32',
          800: '#102F26',
          900: '#0B1F19',
        },
        terracotta: {
          DEFAULT: '#C2413B',
          50: '#FDF5F5',
          100: '#FCEBEA',
          200: '#F8D4D2',
          300: '#F1AFA9',
          400: '#E77C72',
          500: '#D95349',
          600: '#C2413B',
          700: '#A3332D',
          800: '#832722',
          900: '#641B17',
        },
        charcoal: {
          DEFAULT: '#202824',
          50: '#F8FAF9',
          100: '#EEF2F0',
          200: '#DCE3E0',
          300: '#BCC7C2',
          400: '#8F9E97',
          500: '#66736C', // Secondary text
          600: '#4C5852',
          700: '#38433E',
          800: '#2A332E',
          900: '#202824', // Main text
        },
        'warm-grey': {
          DEFAULT: '#E3E9E4',
          50: '#FAFBF9',
          100: '#F2F5F3',
          200: '#E3E9E4', // Core border
          300: '#D0D8D2',
          400: '#B0BCB3',
          500: '#8E9C92',
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          '"JetBrains Mono"',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'monospace',
        ],
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgba(32, 40, 36, 0.04)',
        card: '0 1px 3px 0 rgba(32, 40, 36, 0.06), 0 1px 2px -1px rgba(32, 40, 36, 0.04)',
        elevated: '0 4px 6px -1px rgba(32, 40, 36, 0.07), 0 2px 4px -2px rgba(32, 40, 36, 0.05)',
      }
    },
  },
  plugins: [],
}
