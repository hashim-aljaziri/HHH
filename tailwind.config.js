/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        turquoise: '#0891b2',
        qurra: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          900: '#166534',
        },
      },
      fontFamily: {
        serif: ['Playfair Display', 'Lora', 'Georgia', 'serif'],
        sans: ['Poppins', 'Montserrat', 'system-ui', 'sans-serif'],
        arabic: ['Cairo', 'Amiri', 'Tajawal', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      },
    },
  },
  plugins: [],
  safelist: [
    'dark',
    'light',
    'pink',
    'ocean',
    'sand',
    'forest',
  ],
};
