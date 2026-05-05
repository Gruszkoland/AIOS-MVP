import Link from "next/link";

import { AnalysisResult } from "@/lib/mock-analysis";

export function AnalysisPreview({ result }: { result: AnalysisResult }) {
  return (
    <div className="grid gap-6">
      <section className="panel p-6 lg:p-8">
        <div className="flex flex-col gap-3 border-b border-[color:var(--border)] pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Analysis result</p>
            <h1 className="mt-2 text-4xl tracking-[-0.04em]">{result.fileName}</h1>
          </div>
          <div className="flex gap-3 text-sm text-[color:var(--muted)]">
            <span>{result.parseMode === "real" ? "real parser" : "mock parser"}</span>
            <span>{result.fileSizeKb} KB</span>
            <span>{result.estimatedPages} pages</span>
            <span>{result.confidence}% confidence</span>
          </div>
        </div>

        <div className="grid gap-6 pt-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-5">
            <div>
              <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Verdict</p>
              <p className="mt-2 text-2xl font-semibold">{result.verdict}</p>
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Summary</p>
              <p className="mt-2 max-w-3xl text-lg leading-8">{result.summary}</p>
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Target outcome</p>
              <p className="mt-2 text-base leading-7 text-[color:var(--muted)]">{result.targetOutcome}</p>
            </div>
            {result.textSample ? (
              <div>
                <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Extracted sample</p>
                <p className="mt-2 rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-sm leading-7 text-[color:var(--muted)]">
                  {result.textSample}
                </p>
              </div>
            ) : null}
          </div>
          <aside className="metric-card p-5">
            <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Premium unlock</p>
            <ul className="mt-4 space-y-3 text-sm leading-6">
              {result.premiumUnlock.map((item) => (
                <li key={item}>+ {item}</li>
              ))}
            </ul>
            <Link href="/pricing" className="cta-primary mt-6 w-full">
              Unlock premium plan
            </Link>
          </aside>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="panel p-6 lg:p-8">
          <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Signals found</p>
          <ul className="mt-4 space-y-4 text-base leading-7">
            {result.insights.map((item) => (
              <li key={item} className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="panel p-6 lg:p-8">
          <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Next steps</p>
          <ol className="mt-4 space-y-4 text-base leading-7">
            <li className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
              Send the summary to one stakeholder who would normally avoid reading the source document.
            </li>
            <li className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
              Validate whether the verdict matches the real business decision process.
            </li>
            <li className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
              If the value is clear, connect billing next and gate export or repeat usage.
            </li>
          </ol>
        </div>
      </section>
    </div>
  );
}
