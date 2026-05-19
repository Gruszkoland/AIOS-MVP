"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { getOrCreateUserId } from "@/lib/client-user-id";
import { trackFunnelEvent } from "@/lib/funnel-client";

type AnalyzeResponse = {
  id: string;
  fileName: string;
  fileSizeKb: number;
  estimatedPages: number;
  confidence: number;
  parseMode?: "real" | "mock";
  summary: string;
  verdict: string;
  insights: string[];
  premiumUnlock: string[];
  targetOutcome: string;
  usage?: {
    plan: "free" | "pro" | "founding";
    usedToday: number;
    limit: number | null;
  };
};

type UsageResponse = {
  userId: string;
  plan: "free" | "pro" | "founding";
  usedToday: number;
  remainingToday: number | null;
  limit: number | null;
};

export function UploadForm() {
  const router = useRouter();
  const [goal, setGoal] = useState("Find the decision blockers and highlight the parts to send upstream.");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [usage, setUsage] = useState<UsageResponse | null>(null);

  useEffect(() => {
    const userId = getOrCreateUserId();

    void fetch("/api/usage", {
      headers: {
        "x-user-id": userId,
      },
    })
      .then((response) => response.json())
      .then((payload) => setUsage(payload as UsageResponse))
      .catch(() => {
        setUsage(null);
      });
  }, []);

  const helperText = useMemo(() => {
    if (!file) {
      return "Upload one PDF up to 10 MB. This MVP uses a mock analyzer so you can validate flow before adding real extraction.";
    }

    return `${file.name} selected · ${Math.max(1, Math.round(file.size / 1024))} KB`;
  }, [file]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!file) {
      setError("Choose a PDF file before starting the analysis.");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("goal", goal);

    try {
      const userId = getOrCreateUserId();
      void trackFunnelEvent("analysis_submit", {
        hasFile: true,
      });

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
        headers: {
          "x-user-id": userId,
        },
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { error?: string } | null;
        throw new Error(payload?.error || "Analysis failed. Try again.");
      }

      const payload = (await response.json()) as AnalyzeResponse;
      void trackFunnelEvent("analysis_success", {
        parseMode: payload.parseMode || "mock",
      });

      if (payload.usage) {
        setUsage({
          userId: getOrCreateUserId(),
          plan: payload.usage.plan,
          usedToday: payload.usage.usedToday,
          remainingToday: payload.usage.limit === null ? null : Math.max(0, payload.usage.limit - payload.usage.usedToday),
          limit: payload.usage.limit,
        });
      }

      const searchParams = new URLSearchParams({
        payload: encodeURIComponent(JSON.stringify(payload)),
      });
      router.push(`/result?${searchParams.toString()}`);
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : "Unexpected error during upload.";
      setError(message);
      void trackFunnelEvent("analysis_error", {
        message,
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="panel flex flex-col gap-5 p-6 lg:p-8">
      <div>
        <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Upload a PDF</p>
        <h2 className="mt-3 text-3xl tracking-[-0.03em]">Run the core MVP flow</h2>
      </div>

      {usage ? (
        <div className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm text-[color:var(--muted)]">
          Plan: <strong className="text-[color:var(--foreground)]">{usage.plan}</strong>
          {usage.limit !== null ? ` · Used today: ${usage.usedToday}/${usage.limit}` : " · Unlimited analyses"}
        </div>
      ) : null}

      <label className="flex flex-col gap-2 text-sm font-medium">
        <span>Decision goal</span>
        <textarea
          value={goal}
          onChange={(event) => setGoal(event.target.value)}
          rows={4}
          className="min-h-28 rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-base outline-none transition focus:border-[color:var(--accent)]"
          placeholder="Example: summarize pricing risk, missed clauses, and urgency level."
        />
      </label>

      <label className="flex cursor-pointer flex-col gap-3 rounded-3xl border border-dashed border-[color:var(--border)] bg-[color:var(--surface)] px-5 py-8 text-center transition hover:border-[color:var(--accent)]">
        <span className="text-base font-semibold">Drop a PDF or click to browse</span>
        <span className="text-sm text-[color:var(--muted)]">{helperText}</span>
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
        />
      </label>

      {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}

      <button type="submit" disabled={isSubmitting} className="cta-primary w-full border-none disabled:cursor-wait disabled:opacity-70">
        {isSubmitting ? "Analyzing..." : "Analyze PDF"}
      </button>
    </form>
  );
}
