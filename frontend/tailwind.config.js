/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#050505",
        foreground: "#ffffff",
        primary: {
          DEFAULT: "#00f2ff",
          foreground: "#000000",
        },
        secondary: {
          DEFAULT: "#7000ff",
          foreground: "#ffffff",
        },
        accent: {
          DEFAULT: "#ff00d4",
          foreground: "#ffffff",
        },
        muted: {
          DEFAULT: "#1a1a1a",
          foreground: "#a1a1aa",
        },
        card: {
          DEFAULT: "rgba(20, 20, 20, 0.8)",
          foreground: "#ffffff",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        'hud': '0 0 20px rgba(0, 242, 255, 0.2)',
        'hud-lg': '0 0 40px rgba(0, 242, 255, 0.3)',
      }
    },
  },
  plugins: [],
}
