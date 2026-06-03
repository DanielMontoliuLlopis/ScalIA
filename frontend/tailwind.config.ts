import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f5f3ff",
          100: "#ede9fe",
          200: "#ddd6fe",
          300: "#c4b5fd",
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
          700: "#6d28d9",
        },
        accent: {
          cyan: "#06b6d4",
          violet: "#8b5cf6",
        },
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%)",
        "app-gradient":
          "radial-gradient(1200px 600px at 0% 0%, rgba(139,92,246,0.18), transparent 55%), radial-gradient(1000px 700px at 100% 100%, rgba(6,182,212,0.16), transparent 55%)",
      },
      boxShadow: {
        glass: "0 8px 32px rgba(31, 38, 135, 0.12)",
        "glass-lg": "0 16px 48px rgba(31, 38, 135, 0.18)",
        glow: "0 8px 24px rgba(124, 58, 237, 0.35)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
} satisfies Config;
