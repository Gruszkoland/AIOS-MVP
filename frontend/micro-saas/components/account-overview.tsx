"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getOrCreateUserId } from "@/lib/client-user-id";

type UsagePayload = {
  userId: string;
  plan: "free" | "pro" | "founding";
  usedToday: number;
  remainingToday: number | null;
  limit: number | null;
};

type BillingPayload = {
  userId: string;
  count: number;
  events: Array<{
    stripeEventId: string;
    stripeEventType: string;
    accessState: "active" | "canceled" | "payment_received" | "ignored";
    plan: string;
    createdAt: string;
  }>;
};

type AnalysesPayload = {
  count: number;
  entries: Array<{ id: string; createdAt: string }>;
};

type FunnelPayload = {
  count: number;
  events: Array<{
    id: string;
    name: string;
    createdAt: string;
  }>;
};

type FunnelSummaryPayload = {
  userId: string;
  summary: {
    homeViews: number;
    uploadViews: number;
    pricingViews: number;
    analysisSubmits: number;
    analysisSuccesses: number;
    checkoutStarts: number;
    checkoutSuccesses: number;
    analysisSuccessRate: number;
    checkoutConversionRate: number;
  };
};

export function AccountOverview() {
  const [usage, setUsage] = useState<UsagePayload | null>(null);
  const [billing, setBilling] = useState<BillingPayload | null>(null);
  const [analyses, setAnalyses] = useState<AnalysesPayload | null>(null);
  const [funnel, setFunnel] = useState<FunnelPayload | null>(null);
  const [funnelSummary, setFunnelSummary] = useState<FunnelSummaryPayload | null>(null);
  const [isExporting, setIsExporting] = useState<"json" | "csv" | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const userId = getOrCreateUserId();

    Promise.all([
      fetch("/api/usage", { headers: { "x-user-id": userId } }).then((response) => response.json() as Promise<UsagePayload>),
      fetch("/api/billing-events?limit=5", { headers: { "x-user-id": userId } }).then(
        (response) => response.json() as Promise<BillingPayload>,
      ),
      fetch("/api/analyses?limit=5", { headers: { "x-user-id": userId } }).then(
        (response) => response.json() as Promise<AnalysesPayload>,
      ),
      fetch("/api/funnel-events?limit=6", { headers: { "x-user-id": userId } }).then(
        (response) => response.json() as Promise<FunnelPayload>,
      ),
      fetch("/api/funnel-summary", { headers: { "x-user-id": userId } }).then(
        (response) => response.json() as Promise<FunnelSummaryPayload>,
      ),
    ])
      .then(([usagePayload, billingPayload, analysesPayload, funnelPayload, funnelSummaryPayload]) => {
        setUsage(usagePayload);
        setBilling(billingPayload);
        setAnalyses(analysesPayload);
        setFunnel(funnelPayload);
        setFunnelSummary(funnelSummaryPayload);
      })
      .catch(() => {
        setError("Could not load account data right now.");
      });
  }, []);

  if (error) {
    return <div className="panel p-8 text-red-800">{error}</div>;
  }

  if (!usage || !billing || !analyses || !funnel || !funnelSummary) {
    return <div className="panel p-8">Loading account...</div>;
  }

  async function exportReport(format: "json" | "csv") {
    const userId = getOrCreateUserId();
    setIsExporting(format);

    try {
      const response = await fetch(`/api/funnel-export?format=${format}`, {
        headers: {
          "x-user-id": userId,
        },
      });

      if (!response.ok) {
        throw new Error("Export failed.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `funnel-report-${userId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Could not export report right now.");
    } finally {
      setIsExporting(null);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-3">
        <article className="panel p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">User</p>
          <p className="mt-3 text-sm break-all">{usage.userId}</p>
        </article>
        <article className="panel p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">Plan</p>
          <p className="mt-3 text-2xl capitalize">{usage.plan}</p>
        </article>
        <article className="panel p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">Today usage</p>
          <p className="mt-3 text-2xl">{usage.limit === null ? `${usage.usedToday} (unlimited)` : `${usage.usedToday}/${usage.limit}`}</p>
        </article>
      </section>

      <section className="panel p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl tracking-[-0.03em]">Recent billing events</h2>
          <Link href="/pricing" className="cta-secondary">
            Open pricing
          </Link>
        </div>
        {billing.events.length === 0 ? (
          <p className="mt-4 text-[color:var(--muted)]">No billing events for this user yet.</p>
        ) : (
          <ul className="mt-4 grid gap-3">
            {billing.events.map((event) => (
              <li key={event.stripeEventId} className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm">
                <strong>{event.accessState}</strong> · {event.plan} · {event.stripeEventType}
                <div className="text-[color:var(--muted)] mt-1">{new Date(event.createdAt).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl tracking-[-0.03em]">Recent analyses</h2>
          <Link href="/history" className="cta-secondary">
            Open history
          </Link>
        </div>
        <p className="mt-4 text-[color:var(--muted)]">Stored analyses for this user: {analyses.count}</p>
      </section>

      <section className="panel p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl tracking-[-0.03em]">Funnel KPIs</h2>
          <div className="flex gap-2">
            <button
              onClick={() => exportReport("json")}
              disabled={isExporting !== null}
              className="cta-secondary disabled:cursor-wait disabled:opacity-70"
            >
              {isExporting === "json" ? "Exporting JSON..." : "Export JSON"}
            </button>
            <button
              onClick={() => exportReport("csv")}
              disabled={isExporting !== null}
              className="cta-secondary disabled:cursor-wait disabled:opacity-70"
            >
              {isExporting === "csv" ? "Exporting CSV..." : "Export CSV"}
            </button>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm">
            Analysis success rate: <strong>{funnelSummary.summary.analysisSuccessRate}%</strong>
          </div>
          <div className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm">
            Checkout conversion rate: <strong>{funnelSummary.summary.checkoutConversionRate}%</strong>
          </div>
          <div className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm">
            Checkout starts: <strong>{funnelSummary.summary.checkoutStarts}</strong>
          </div>
          <div className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm">
            Checkout successes: <strong>{funnelSummary.summary.checkoutSuccesses}</strong>
          </div>
        </div>
      </section>

      <section className="panel p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl tracking-[-0.03em]">Funnel activity</h2>
          <span className="text-sm text-[color:var(--muted)]">Last {funnel.count} events</span>
        </div>
        {funnel.events.length === 0 ? (
          <p className="mt-4 text-[color:var(--muted)]">No funnel events captured for this user yet.</p>
        ) : (
          <ul className="mt-4 grid gap-3">
            {funnel.events.map((event) => (
              <li key={event.id} className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm">
                <strong>{event.name}</strong>
                <div className="text-[color:var(--muted)] mt-1">{new Date(event.createdAt).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
