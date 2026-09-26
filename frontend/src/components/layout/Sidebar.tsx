"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/components/ui/cn";
import { Diamond } from "@/components/ui/Motifs";

import { BackendStatus } from "./BackendStatus";
import { Logo } from "./Logo";
import { NAV_ITEMS } from "./nav";

export function Sidebar() {
  const pathname = usePathname();
  const isActive = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-line bg-paper">
      <Link href="/" className="block px-6 pt-7 pb-4" aria-label="Burhan home">
        <Logo priority className="w-40" />
      </Link>
      <p className="px-6 text-[11px] leading-relaxed tracking-wide text-muted">
        Agentic AI Research Scientist
        <br />
        <span className="text-faint">Building living Research Digital Twins</span>
      </p>

      <div className="mx-6 my-5 flex items-center gap-2 text-line-strong">
        <span className="h-px flex-1 bg-line" />
        <Diamond size={6} />
        <span className="h-px flex-1 bg-line" />
      </div>

      <nav className="flex-1 space-y-0.5 px-3">
        {NAV_ITEMS.map(({ href, label, description, icon: Icon }) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors",
                active ? "bg-ink text-paper" : "text-ink-2 hover:bg-paper-2",
              )}
            >
              <Icon className={cn("size-4", active ? "text-paper" : "text-muted group-hover:text-ink")} />
              <span className="flex flex-col">
                <span className="text-sm font-medium">{label}</span>
                <span className={cn("text-[11px]", active ? "text-paper/60" : "text-faint")}>
                  {description}
                </span>
              </span>
            </Link>
          );
        })}
      </nav>

      <BackendStatus />
    </aside>
  );
}
