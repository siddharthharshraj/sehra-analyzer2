"use client";

import dynamic from "next/dynamic";

const CopilotSidebar = dynamic(
  () =>
    import("./copilot-sidebar").then((m) => m.CopilotSidebar),
  { ssr: false },
);

export function LazyCopilotSidebar() {
  return <CopilotSidebar />;
}
