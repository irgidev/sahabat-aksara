
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Quicksand", "sans-serif"],
      },
      colors: {
        pastel: {
          sky: "#87CEEB",
          mint: "#A8E6CF",
          peach: "#FFD3B6",
          lavender: "#DCD3FF",
          pink: "#FFAAA5",
          yellow: "#FFF3B0",
        },
      },
      boxShadow: {
        glass: "0 8px 32px 0 rgba(31, 38, 135, 0.07)",
        "glass-strong": "0 12px 40px 0 rgba(31, 38, 135, 0.12)",
        "glow-mint": "0 0 40px rgba(168, 230, 207, 0.6)",
        "glow-yellow": "0 0 30px rgba(255, 243, 176, 0.8)",
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        "float-delayed": "float 6s ease-in-out 3s infinite",
        shake: "shake 0.5s cubic-bezier(.36,.07,.19,.97) both",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-15px)" },
        },
        shake: {
          "10%, 90%": { transform: "translate3d(-1px, 0, 0)" },
          "20%, 80%": { transform: "translate3d(2px, 0, 0)" },
          "30%, 50%, 70%": { transform: "translate3d(-4px, 0, 0)" },
          "40%, 60%": { transform: "translate3d(4px, 0, 0)" }
        }
      },
    },
  },
  plugins: [],
}
