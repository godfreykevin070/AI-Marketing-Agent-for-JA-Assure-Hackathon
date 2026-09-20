/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#080f1c",
          900: "#0c1729",
          800: "#121f36",
          700: "#1b2c47",
          600: "#26395a",
        },
        accent: {
          DEFAULT: "#5eead4",
          soft: "#99f6e4",
          dim: "#2dd4bf",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};