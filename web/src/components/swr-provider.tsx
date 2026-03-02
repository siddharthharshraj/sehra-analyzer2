"use client";

import { SWRConfig } from "swr";
import type { ReactNode } from "react";

export function SWRProvider({ children }: { children: ReactNode }) {
  return (
    <SWRConfig
      value={{
        // Deduplicate identical requests within 5 seconds
        dedupingInterval: 5000,
        // Don't refetch on window focus (reduces unnecessary API calls)
        revalidateOnFocus: false,
        // Retry failed requests up to 2 times
        errorRetryCount: 2,
        // Keep previous data while revalidating (avoids loading flashes)
        keepPreviousData: true,
      }}
    >
      {children}
    </SWRConfig>
  );
}
