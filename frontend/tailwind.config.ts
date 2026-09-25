import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17211c",
        moss: "#355c4a",
        clay: "#b46848",
        paper: "#f7f5ef",
        line: "#d7d4cb"
      }
    }
  },
  plugins: []
};

export default config;
