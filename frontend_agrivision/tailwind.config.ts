import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        "av-bg": "var(--av-bg)",
        "av-surface": "var(--av-surface)",
        "av-foreground": "var(--av-foreground)",
        "av-muted": "var(--av-muted)",
        "av-accent": "var(--av-accent)",
        "av-sidebar": "var(--av-sidebar)",
      },
    },
  },
  plugins: [],
};

export default config;