import Image from "next/image";

import { cn } from "@/components/ui/cn";

/**
 * The official Burhan logo, rendered unmodified. `mix-blend-multiply` lets its white
 * background melt into the warm paper surface without altering the artwork.
 */
export function Logo({ className, priority }: { className?: string; priority?: boolean }) {
  return (
    <Image
      src="/burhan-logo.webp"
      alt="Burhan — برهان"
      width={1548}
      height={1016}
      priority={priority}
      className={cn("h-auto mix-blend-multiply select-none", className)}
    />
  );
}
