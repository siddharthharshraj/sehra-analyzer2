"use client";

import { Eye, ChevronDown } from "lucide-react";

export function HeroSection() {
  return (
    <section
      className="relative flex min-h-screen flex-col items-center justify-center px-4 text-white overflow-hidden"
      style={{
        background:
          "linear-gradient(135deg, #095456 0%, #0D7377 50%, #10857A 100%)",
      }}
    >
      {/* Decorative glow rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="h-[500px] w-[500px] rounded-full bg-white/[0.03] blur-3xl" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="h-[300px] w-[300px] rounded-full bg-white/[0.04] blur-2xl" />
      </div>

      <div className="relative z-10 flex flex-col items-center text-center animate-[fadeSlideUp_0.6s_ease-out_both]">
        {/* Logo with glow */}
        <div className="relative mb-8">
          <div className="absolute inset-0 rounded-2xl bg-white/20 blur-xl scale-150" />
          <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-white/15 backdrop-blur-sm border border-white/20 shadow-lg shadow-black/10">
            <Eye className="h-10 w-10 text-white drop-shadow-lg" />
          </div>
        </div>

        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl md:text-7xl">
          SEHRA Analyzer
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-white/80 sm:text-xl md:text-2xl font-light">
          AI-Powered School Eye Health Rapid Assessment Analysis
        </p>

        {/* Tagline pill */}
        <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/15 px-5 py-2.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-300 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="text-sm font-medium tracking-wide text-white/90">
            Reducing analysis time from 2 months to 2 days
          </span>
        </div>

        <p className="mt-8 text-sm text-white/50">
          Built by{" "}
          <a
            href="https://samanvayfoundation.org"
            target="_blank"
            rel="noopener noreferrer"
            className="underline decoration-white/30 hover:text-white/70 transition-colors"
          >
            Samanvay Foundation
          </a>{" "}
          for{" "}
          <span className="text-white/60">PRASHO Foundation</span>
        </p>
      </div>

      {/* Scroll indicator */}
      <button
        onClick={() =>
          document
            .getElementById("section-challenge")
            ?.scrollIntoView({ behavior: "smooth" })
        }
        className="absolute bottom-10 z-10 flex flex-col items-center gap-1 text-white/40 hover:text-white/70 transition-colors cursor-pointer"
        aria-label="Scroll down"
      >
        <span className="text-xs tracking-widest uppercase">Scroll</span>
        <ChevronDown className="h-5 w-5 animate-bounce" />
      </button>
    </section>
  );
}
