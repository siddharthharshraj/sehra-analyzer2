"use client";

import { cn } from "@/lib/utils";

interface WizardStepperProps {
  steps: string[];
  currentStep: number;
  onStepClick: (step: number) => void;
}

export function WizardStepper({
  steps,
  currentStep,
  onStepClick,
}: WizardStepperProps) {
  return (
    <div className="flex items-center justify-center gap-1">
      {steps.map((label, i) => (
        <div key={i} className="flex items-center">
          <button
            type="button"
            onClick={() => onStepClick(i)}
            className={cn(
              "flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
              i === currentStep
                ? "bg-[#0D7377] text-white"
                : i < currentStep
                  ? "bg-[#0D7377]/10 text-[#0D7377]"
                  : "bg-muted text-muted-foreground",
            )}
          >
            <span
              className={cn(
                "flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold",
                i === currentStep
                  ? "bg-white text-[#0D7377]"
                  : i < currentStep
                    ? "bg-[#0D7377] text-white"
                    : "bg-muted-foreground/20",
              )}
            >
              {i + 1}
            </span>
            <span className="hidden sm:inline">{label}</span>
          </button>
          {i < steps.length - 1 && (
            <div
              className={cn(
                "mx-1 h-px w-6",
                i < currentStep ? "bg-[#0D7377]" : "bg-border",
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
