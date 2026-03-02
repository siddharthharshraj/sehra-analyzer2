"use client";

import { Suspense } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { CopilotProvider, useCopilotContext } from "@/components/copilot/copilot-context";
import { LazyCopilotSidebar } from "@/components/copilot/copilot-sidebar-lazy";
import { useSidebarCollapsed } from "@/lib/sidebar-store";
import { cn } from "@/lib/utils";

function AppLayoutInner({ children }: { children: React.ReactNode }) {
  const { collapsed } = useSidebarCollapsed();
  const { isOpen: copilotOpen } = useCopilotContext();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div
        className={cn(
          "transition-all duration-200",
          collapsed ? "lg:pl-16" : "lg:pl-64",
          copilotOpen && "lg:pr-[380px]",
        )}
      >
        <Header />
        <main className="p-6">
          <Suspense>{children}</Suspense>
        </main>
      </div>
      <LazyCopilotSidebar />
    </div>
  );
}

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <CopilotProvider>
      <AppLayoutInner>{children}</AppLayoutInner>
    </CopilotProvider>
  );
}
