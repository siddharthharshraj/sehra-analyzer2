"use client";

import { useState, useCallback, useRef } from "react";
import { createSSEStream } from "@/lib/api-client";
import type { AnalysisEvent } from "@/lib/types";

interface SSEState {
  status: "idle" | "running" | "complete" | "error";
  step: number;
  totalSteps: number;
  label: string;
  progress: number;
  sehraId: string | null;
  enablerCount: number;
  barrierCount: number;
  errorMessage: string | null;
}

const initialState: SSEState = {
  status: "idle",
  step: 0,
  totalSteps: 0,
  label: "",
  progress: 0,
  sehraId: null,
  enablerCount: 0,
  barrierCount: 0,
  errorMessage: null,
};

export function useSSE() {
  const [state, setState] = useState<SSEState>(initialState);
  const controllerRef = useRef<AbortController | null>(null);

  const startUpload = useCallback((file: File) => {
    setState({ ...initialState, status: "running" });

    const formData = new FormData();
    formData.append("file", file);

    controllerRef.current = createSSEStream(
      "/analyze/upload",
      formData,
      (event) => handleEvent(event as AnalysisEvent),
      (error) =>
        setState((prev) => ({
          ...prev,
          status: "error",
          errorMessage: error.message,
        })),
    );
  }, []);

  const startFormAnalysis = useCallback((formData: Record<string, unknown>) => {
    setState({ ...initialState, status: "running" });

    controllerRef.current = createSSEStream(
      "/analyze/form",
      JSON.stringify(formData),
      (event) => handleEvent(event as AnalysisEvent),
      (error) =>
        setState((prev) => ({
          ...prev,
          status: "error",
          errorMessage: error.message,
        })),
    );
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    setState(initialState);
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  function handleEvent(event: AnalysisEvent) {
    if (event.event === "progress") {
      setState((prev) => ({
        ...prev,
        step: event.step,
        totalSteps: event.total_steps,
        label: event.label,
        progress: event.progress,
      }));
    } else if (event.event === "complete") {
      setState((prev) => ({
        ...prev,
        status: "complete",
        sehraId: event.sehra_id,
        enablerCount: event.enabler_count,
        barrierCount: event.barrier_count,
        progress: 1,
      }));
    } else if (event.event === "error") {
      setState((prev) => ({
        ...prev,
        status: "error",
        errorMessage: event.message,
      }));
    }
  }

  return { ...state, startUpload, startFormAnalysis, cancel, reset };
}
