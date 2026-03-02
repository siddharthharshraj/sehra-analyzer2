"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Eye, Loader2, AlertCircle, Clock } from "lucide-react";
import { PasscodeForm } from "@/components/share/passcode-form";
import { ReportViewer } from "@/components/share/report-viewer";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function BrandedMessage({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{
        background:
          "linear-gradient(135deg, #095456 0%, #0D7377 50%, #10857A 100%)",
      }}
    >
      <div className="w-full max-w-sm rounded-xl border bg-white p-8 text-center shadow-lg">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#0D7377]">
          <Eye className="h-6 w-6 text-white" />
        </div>
        <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-red-50">
          <Icon className="h-5 w-5 text-red-500" />
        </div>
        <h1 className="text-xl font-semibold">{title}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
        <p className="mt-4 text-xs text-muted-foreground">
          Please request a new link from the report owner.
        </p>
      </div>
    </div>
  );
}

export default function SharePage() {
  const params = useParams();
  const token = params.token as string;

  const [state, setState] = useState<
    "loading" | "passcode" | "viewing" | "invalid" | "expired"
  >("loading");
  const [html, setHtml] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/public/share/${token}`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.valid) {
          setState("invalid");
        } else if (data.expired) {
          setState("expired");
        } else {
          setState("passcode");
        }
      })
      .catch(() => setState("invalid"));
  }, [token]);

  async function handlePasscode(passcode: string) {
    setError(null);
    const res = await fetch(`${API_BASE}/public/share/${token}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passcode }),
    });

    if (res.status === 429) {
      setError("Too many failed attempts. Please try again later.");
      return;
    }

    if (res.status === 410) {
      setState("expired");
      return;
    }

    const data = await res.json();
    if (data.success && data.html) {
      setHtml(data.html);
      setState("viewing");
    } else {
      setError("Incorrect passcode");
    }
  }

  if (state === "loading") {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        style={{
          background:
            "linear-gradient(135deg, #095456 0%, #0D7377 50%, #10857A 100%)",
        }}
      >
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-white" />
          <p className="text-sm text-white/80">Loading report...</p>
        </div>
      </div>
    );
  }

  if (state === "invalid") {
    return (
      <BrandedMessage
        icon={AlertCircle}
        title="Invalid Link"
        description="This share link is invalid or has been revoked."
      />
    );
  }

  if (state === "expired") {
    return (
      <BrandedMessage
        icon={Clock}
        title="Link Expired"
        description="This share link has expired and is no longer accessible."
      />
    );
  }

  if (state === "viewing") {
    return <ReportViewer html={html} />;
  }

  return <PasscodeForm onSubmit={handlePasscode} error={error} />;
}
