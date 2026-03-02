"use client";

import useSWR from "swr";
import { apiGet } from "@/lib/api-client";
import type {
  SEHRASummary,
  SEHRADetail,
  ComponentAnalysis,
  ExecutiveSummary,
} from "@/lib/types";

const fetcher = <T>(path: string) => apiGet<T>(path);

export function useSehras() {
  const { data, error, isLoading, mutate } = useSWR<SEHRASummary[]>(
    "/sehras",
    fetcher,
  );
  return { sehras: data || [], error, isLoading, mutate };
}

export function useSehra(id: string | null) {
  const { data, error, isLoading, mutate } = useSWR<SEHRADetail>(
    id ? `/sehras/${id}` : null,
    fetcher,
  );
  return { sehra: data, error, isLoading, mutate };
}

export function useComponents(sehraId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<ComponentAnalysis[]>(
    sehraId ? `/sehras/${sehraId}/components` : null,
    fetcher,
  );
  return { components: data || [], error, isLoading, mutate };
}

export function useSummary(sehraId: string | null) {
  const { data, error, isLoading } = useSWR<ExecutiveSummary>(
    sehraId ? `/sehras/${sehraId}/summary` : null,
    fetcher,
  );
  return { summary: data, error, isLoading };
}
