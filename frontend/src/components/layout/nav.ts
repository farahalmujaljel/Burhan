import { FileText, History, type LucideIcon, Network, Search, Sparkles } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Research Twin", description: "Living model of the field", icon: Sparkles },
  { href: "/papers", label: "Papers", description: "Ingest & extract", icon: FileText },
  { href: "/graph", label: "Knowledge Graph", description: "Explore relationships", icon: Network },
  { href: "/evidence", label: "Evidence", description: "Semantic search", icon: Search },
  { href: "/updates", label: "Twin Evolution", description: "How the twin changed", icon: History },
];
