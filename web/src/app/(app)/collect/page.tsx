"use client";

import { useState, useEffect, useCallback } from "react";
import useSWR from "swr";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiGet, apiPut } from "@/lib/api-client";
import { COMPONENTS, COMPONENT_LABELS } from "@/lib/constants";
import { WizardStepper } from "@/components/collect/wizard-stepper";
import { HeaderForm } from "@/components/collect/header-form";
import { SectionForm } from "@/components/collect/section-form";
import { AnalysisProgress } from "@/components/upload/analysis-progress";
import { useSSE } from "@/hooks/use-sse";
import type { CodebookItem, FormDraft } from "@/lib/types";
import type { ComponentName } from "@/lib/constants";

const STEPS = [
  "Details",
  ...COMPONENTS.map((c) => COMPONENT_LABELS[c]),
];

export default function CollectPage() {
  const [step, setStep] = useState(0);
  const [header, setHeader] = useState<Record<string, string>>({});
  const [responses, setResponses] = useState<
    Record<string, { answer: string; remark: string }>
  >({});

  const sse = useSSE();

  // Load codebook items
  const { data: sections } = useSWR<string[]>(
    "/codebook/sections",
    (url: string) => apiGet<string[]>(url),
  );

  // Load items per section
  const [sectionItems, setSectionItems] = useState<
    Record<string, CodebookItem[]>
  >({});

  useEffect(() => {
    if (!sections) return;
    Promise.all(
      sections.map((s) =>
        apiGet<CodebookItem[]>(`/codebook/items?section=${s}`).then(
          (items) => [s, items] as const,
        ),
      ),
    ).then((results) => {
      const map: Record<string, CodebookItem[]> = {};
      results.forEach(([s, items]) => {
        map[s] = items;
      });
      setSectionItems(map);
    });
  }, [sections]);

  // Load draft
  useEffect(() => {
    apiGet<FormDraft | null>("/drafts")
      .then((draft) => {
        if (draft) {
          setStep(draft.section_progress);
          setResponses(
            draft.responses as Record<
              string,
              { answer: string; remark: string }
            >,
          );
        }
      })
      .catch(() => {});
  }, []);

  // Auto-save draft
  const saveDraft = useCallback(async () => {
    try {
      await apiPut("/drafts", {
        section_progress: step,
        responses,
      });
    } catch {
      // silent
    }
  }, [step, responses]);

  useEffect(() => {
    const timer = setTimeout(saveDraft, 2000);
    return () => clearTimeout(timer);
  }, [saveDraft]);

  function handleSubmit() {
    const formData = {
      header,
      responses,
    };
    sse.startFormAnalysis(formData);
    toast.info("Submitting assessment for analysis...");
  }

  const currentComponent = COMPONENTS[step - 1];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Collect Data</h2>
        <p className="text-sm text-muted-foreground">
          Fill in SEHRA assessment data step by step. Your progress is saved automatically.
        </p>
      </div>

      <WizardStepper
        steps={STEPS}
        currentStep={step}
        onStepClick={setStep}
      />

      {step === 0 && <HeaderForm header={header} onChange={setHeader} />}

      {step > 0 && step <= COMPONENTS.length && currentComponent && (
        <SectionForm
          section={currentComponent}
          items={sectionItems[currentComponent] || []}
          responses={responses}
          onChange={setResponses}
        />
      )}

      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0 || sse.status === "running"}
        >
          Previous
        </Button>

        {step < COMPONENTS.length ? (
          <Button
            onClick={() => setStep((s) => s + 1)}
            className="bg-[#0D7377] hover:bg-[#095456]"
          >
            Next
          </Button>
        ) : (
          <Button
            onClick={handleSubmit}
            className="bg-[#0D7377] hover:bg-[#095456]"
            disabled={sse.status === "running"}
          >
            Submit & Analyze
          </Button>
        )}
      </div>

      <AnalysisProgress
        status={sse.status}
        step={sse.step}
        totalSteps={sse.totalSteps}
        label={sse.label}
        progress={sse.progress}
        sehraId={sse.sehraId}
        enablerCount={sse.enablerCount}
        barrierCount={sse.barrierCount}
        errorMessage={sse.errorMessage}
        onCancel={sse.cancel}
        onReset={sse.reset}
      />
    </div>
  );
}
