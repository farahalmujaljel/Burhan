import type { Metadata } from "next";

export const metadata: Metadata = { title: "Twin Evolution" };

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
