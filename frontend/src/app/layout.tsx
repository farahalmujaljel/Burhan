import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Newsreader } from "next/font/google";

import { Providers } from "@/components/layout/Providers";
import { Sidebar } from "@/components/layout/Sidebar";

import "./globals.css";

const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-newsreader",
  style: ["normal", "italic"],
});
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: { default: "Burhan · Research Digital Twin", template: "%s · Burhan" },
  description:
    "Burhan is an Agentic AI Research Scientist that builds a living, evidence-backed model of a research field.",
  icons: { icon: "/burhan-logo.webp" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${newsreader.variable} ${inter.variable} ${jetbrains.variable}`}>
      <body className="min-h-screen">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="min-w-0 flex-1">
              <div className="mx-auto max-w-[1280px] px-10 py-10">{children}</div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
