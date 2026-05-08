/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        port: {
          blue: '#1B3A5C',
          sky: '#4A90D9',
          steel: '#6B7B8D',
          warning: '#E8A838',
          danger: '#D14343',
          success: '#34A853',
        },
      },
    },
  },
  plugins: [],
}
