"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getOrCreateUserId } from "@/lib/client-user-id";

type Entry = {
  id: string;
  createdAt: string;
  userId: string;
  result: {
    fileName: string;
    parseMode?: "real" | "mock";
    confidence: number;
    estimatedPages: number;
    summary: string;
  };
};

type HistoryPayload = {
  userId: string;
  count: number;
  entries: Entry[];
};

type UsagePayload = {
  plan: "free" | "pro" | "founding";
  usedToday: number;
  limit: number | null;
};

export function HistoryList() {
  const [history, setHistory] = useState<HistoryPayload | null>(null);
  const [usage, setUsage] = useState<UsagePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const userId = getOrCreateUserId();

    Promise.all([
      fetch("/api/analyses?limit=25", {
        headers: {
          "x-user-id": userId,
        },
      }).then((response) => response.json() as Promise<HistoryPayload>),
      fetch("/api/usage", {
        headers: {
          "x-user-id": userId,
        },
      }).then((response) => response.json() as Promise<UsagePayload>),
    ])
      .then(([historyPayload, usagePayload]) => {
        setHistory(historyPayload);
        setUsage(usagePayload);
      })
      .catch(() => {
        setError("Could not load history for this user. Try refreshing.");
      });
  }, []);

  if (error) {
    return <div className="panel p-8 text-red-800">{error}</div>;
  }

  if (!history) {
    return <div className="panel p-8">Loading history...</div>;
  }

  return (
    <div className="grid gap-6">
      <div className="panel p-5 text-sm text-[color:var(--muted)]">
        <p>
          User: <strong className="text-[color:var(--foreground)]">{history.userId}</strong>
        </p>
        {usage ? (
          <p className="mt-2">
            Plan: <strong className="text-[color:var(--foreground)]">{usage.plan}</strong>
            {usage.limit !== null ? ` · Used today: ${usage.usedToday}/${usage.limit}` : " · Unlimited analyses"}
          </p>
        ) : null}
      </div>

      {history.entries.length === 0 ? (
        <div className="panel p-8">
          <p className="text-lg">No analysis history for this user yet. Run the upload flow to create the first entry.</p>
          <Link href="/upload" className="cta-primary mt-5 inline-flex">
            Go to upload
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {history.entries.map((entry) => (
            <article key={entry.id} className="panel p-6">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <h2 className="text-2xl tracking-[-0.03em]">{entry.result.fileName}</h2>
                <p className="text-sm text-[color:var(--muted)]">{new Date(entry.createdAt).toLocaleString()}</p>
              </div>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-[color:var(--muted)]">
                <span className="rounded-full border border-[color:var(--border)] px-3 py-1">{entry.result.parseMode || "mock"} parser</span>
                <span className="rounded-full border border-[color:var(--border)] px-3 py-1">{entry.result.confidence}% confidence</span>
                <span className="rounded-full border border-[color:var(--border)] px-3 py-1">{entry.result.estimatedPages} pages</span>
              </div>
              <p className="mt-4 text-base leading-7 text-[color:var(--muted)]">{entry.result.summary}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
