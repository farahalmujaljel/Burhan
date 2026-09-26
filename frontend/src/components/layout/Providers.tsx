"use client";

import type { ReactNode } from "react";
import { SWRConfig } from "swr";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <SWRConfig value={{ revalidateOnFocus: true, errorRetryCount: 2, dedupingInterval: 1500 }}>
      {children}
    </SWRConfig>
  );
}
