/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f6ff",
          100: "#dbe9ff",
          500: "#3366ff",
          600: "#254edb",
          700: "#1c3ba8",
          900: "#101b3d",
        },
      },
    },
  },
  plugins: [],
}
