/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          light: '#FAF9F6',
          DEFAULT: '#FAF7F0',
          dark: '#F4EFEB',
        },
        paper: '#FDFBF7',
        charcoal: {
          light: '#44403C',
          DEFAULT: '#1C1917',
          dark: '#0C0A09',
        },
        ink: '#0C0A09',
        editorial: {
          gold: '#B45309',      // amber-700
          goldDark: '#78350F',  // amber-900
          red: '#991B1B',       // red-800
          orange: '#C2410C',    // orange-700
          green: '#166534',     // green-800
          border: '#D6D3D1',    // stone-300
          borderLight: '#E7E5E4', // stone-200
        }
      },
      fontFamily: {
        serif: ['Lora', 'Playfair Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderWidth: {
        '3': '3px',
        '6': '6px',
      }
    },
  },
  plugins: [],
}
