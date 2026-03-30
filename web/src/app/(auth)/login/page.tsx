"use client";

import { HeroSection } from "@/components/landing/hero-section";
import { ChallengeSection } from "@/components/landing/challenge-section";
import { ApproachSection } from "@/components/landing/approach-section";
import { SolutionSection } from "@/components/landing/solution-section";
import { PipelineSection } from "@/components/landing/pipeline-section";
import { ImpactSection } from "@/components/landing/impact-section";
import { LoginSection } from "@/components/landing/login-section";

export default function LoginPage() {
  return (
    <div className="scroll-smooth">
      <HeroSection />
      <ChallengeSection />
      <ApproachSection />
      <SolutionSection />
      <PipelineSection />
      <ImpactSection />
      <LoginSection />
    </div>
  );
}
