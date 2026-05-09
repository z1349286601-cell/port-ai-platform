/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'brand': {
          light: '#E0E7FF',
          DEFAULT: '#6366F1',
          strong: '#4F46E5',
          deep: '#4338CA',
        },
        'accent': {
          light: '#EDE9FE',
          DEFAULT: '#8B5CF6',
          strong: '#7C3AED',
        },
      },
      backgroundImage: {
        'gradient-brand': 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
        'gradient-brand-hover': 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
        'gradient-user': 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
        'gradient-ai': 'linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)',
        'gradient-chat-bg': 'linear-gradient(180deg, #EEF2FF 0%, #F5F3FF 100%)',
      },
    },
  },
  plugins: [],
}
