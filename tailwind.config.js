module.exports = {
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        salmon: {
          50: '#fef8f7',
          100: '#fdf0ec',
          200: '#fbdbd2',
          300: '#f9c1b3',
          400: '#f7b7a6',
          500: '#f1886c',
          600: '#e36240',
          700: '#be4828',
          800: '#9d3d25',
          900: '#833724',
        },
        darkgray: '#121212',
      },
      fontFamily: {
        serif: ['Choco Chips', 'serif'],
        sans: ['Choco Chips', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
