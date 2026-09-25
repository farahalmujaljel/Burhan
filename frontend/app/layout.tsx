import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Burhan MVP",
  description: "Agentic AI Research Scientist for FARQ"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
