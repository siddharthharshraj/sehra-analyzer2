"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotContext } from "@/components/copilot/copilot-context";

const pageTitles: Record<string, string> = {
  "/assessments": "Assessments",
  "/upload": "Upload",
  "/collect": "Collect",
  "/settings": "Settings",
  "/admin": "Manage Questions",
};

export function Header() {
  const pathname = usePathname();
  const { toggle, isOpen, sehraLabel } = useCopilotContext();

  // Build breadcrumb for assessment detail pages
  const isAssessmentDetail = /^\/assessments\/[^/]+$/.test(pathname);

  let title: string;
  if (isAssessmentDetail && sehraLabel) {
    title = sehraLabel;
  } else {
    title = pageTitles[pathname] || "SEHRA";
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-white/80 backdrop-blur-sm">
      <div className="flex h-14 items-center justify-between px-6">
        <div>
          {isAssessmentDetail ? (
            <div className="flex items-center gap-1.5 text-sm">
              <Link
                href="/assessments"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Assessments
              </Link>
              <span className="text-muted-foreground">/</span>
              <span className="font-semibold text-lg">{title}</span>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold">{title}</h1>
              <p className="text-[10px] text-muted-foreground -mt-0.5">
                School Eye Health Rapid Assessment
              </p>
            </>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={toggle}
          className={isOpen ? "text-[#0D7377]" : "text-muted-foreground"}
          title="Toggle AI Copilot"
        >
          <Bot className="mr-1.5 h-4 w-4" />
          <span className="hidden sm:inline text-sm">Copilot</span>
        </Button>
      </div>
    </header>
  );
}
