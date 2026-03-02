"use client";

import { useEffect, useRef, useState } from "react";

interface MermaidProps {
  chart: string;
  className?: string;
}

export function Mermaid({ chart, className = "" }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function render() {
      // @ts-expect-error - loaded from CDN
      if (!window.mermaid) {
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
        script.async = true;
        await new Promise<void>((resolve, reject) => {
          script.onload = () => resolve();
          script.onerror = reject;
          document.head.appendChild(script);
        });
      }

      // @ts-expect-error - loaded from CDN
      const mermaid = window.mermaid;
      mermaid.initialize({
        startOnLoad: false,
        theme: "default",
        themeVariables: {
          primaryColor: "#d1faf5",
          primaryTextColor: "#0f172a",
          primaryBorderColor: "#0D7377",
          secondaryColor: "#e0f2f1",
          secondaryTextColor: "#0f172a",
          secondaryBorderColor: "#0D7377",
          tertiaryColor: "#f0fdfa",
          tertiaryTextColor: "#0f172a",
          tertiaryBorderColor: "#0D7377",
          lineColor: "#0D7377",
          textColor: "#0f172a",
          mainBkg: "#d1faf5",
          nodeBorder: "#0D7377",
          clusterBkg: "#f0fdfa",
          clusterBorder: "#0D7377",
          titleColor: "#0f172a",
          edgeLabelBackground: "#ffffff",
          nodeTextColor: "#0f172a",
          fontSize: "14px",
          labelTextColor: "#0f172a",
          actorTextColor: "#0f172a",
          actorBorder: "#0D7377",
          actorBkg: "#d1faf5",
          signalColor: "#0D7377",
          signalTextColor: "#0f172a",
          activationBorderColor: "#0D7377",
          activationBkgColor: "#e0f2f1",
          sequenceNumberColor: "#ffffff",
          noteBkgColor: "#e0f2f1",
          noteTextColor: "#0f172a",
          noteBorderColor: "#0D7377",
        },
        flowchart: { curve: "basis", padding: 16, htmlLabels: true },
        er: { fontSize: 14 },
        sequence: { mirrorActors: false, messageAlign: "center" },
      });

      const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;
      try {
        const { svg: rendered } = await mermaid.render(id, chart);
        if (!cancelled) {
          setSvg(rendered);
          setError(false);
        }
      } catch (e) {
        console.error("Mermaid render error:", e);
        if (!cancelled) {
          setSvg("");
          setError(true);
        }
      }
    }

    render();
    return () => { cancelled = true; };
  }, [chart]);

  if (error) {
    return (
      <pre className={`overflow-x-auto rounded-xl border bg-gray-950 p-5 text-[13px] leading-relaxed text-gray-300 font-mono ${className}`}>
        {chart}
      </pre>
    );
  }

  if (!svg) {
    return (
      <div className={`rounded-xl border bg-gray-50 p-6 text-center text-sm text-muted-foreground ${className}`}>
        Loading diagram...
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className={`overflow-x-auto rounded-xl border bg-white p-4 [&_svg]:mx-auto [&_svg]:max-w-full [&_text]:!fill-slate-900 [&_.nodeLabel]:!text-slate-900 [&_.label]:!text-slate-900 [&_.edgeLabel]:!text-slate-900 [&_.cluster-label]:!text-slate-900 ${className}`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
