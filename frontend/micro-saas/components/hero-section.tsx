import Link from "next/link";

export function HeroSection() {
  return (
    <section className="mx-auto grid w-full max-w-6xl gap-10 px-6 pb-16 pt-10 lg:grid-cols-[1.15fr_0.85fr] lg:px-10 lg:pb-24 lg:pt-14">
      <div className="flex flex-col gap-6">
        <span className="headline-badge">
          <span className="h-2 w-2 rounded-full bg-[color:var(--accent)]" />
          PDF analysis MVP
        </span>
        <div className="space-y-5">
          <h1 className="max-w-3xl text-5xl leading-[0.94] tracking-[-0.04em] sm:text-6xl lg:text-7xl">
            Turn dense PDFs into a clear go or no-go decision in under three minutes.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted)] sm:text-xl">
            This MVP is tuned for early B2B validation. Upload a proposal, policy, or vendor brief and get a focused summary,
            risk markers, and a premium action plan.
          </p>
        </div>
        <div className="flex flex-col gap-4 sm:flex-row">
          <Link href="/upload" className="cta-primary">
            Try the upload flow
          </Link>
          <Link href="/pricing" className="cta-secondary">
            View launch pricing
          </Link>
        </div>
        <div className="grid gap-4 pt-4 sm:grid-cols-3">
          <div className="metric-card p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">Use case</p>
            <p className="mt-3 text-lg font-semibold">Sales and ops PDFs</p>
          </div>
          <div className="metric-card p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">Free limit</p>
            <p className="mt-3 text-lg font-semibold">1 analysis per day</p>
          </div>
          <div className="metric-card p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--muted)]">Premium unlock</p>
            <p className="mt-3 text-lg font-semibold">Decision memo export</p>
          </div>
        </div>
      </div>
      <div className="panel relative overflow-hidden p-6 lg:p-8">
        <div className="space-y-5">
          <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">What the MVP returns</p>
          <div className="space-y-4">
            <div className="metric-card p-4">
              <p className="text-sm text-[color:var(--muted)]">Executive summary</p>
              <p className="mt-2 text-lg font-semibold">One paragraph for stakeholders who will not read the full document.</p>
            </div>
            <div className="metric-card p-4">
              <p className="text-sm text-[color:var(--muted)]">Risk scan</p>
              <p className="mt-2 text-lg font-semibold">Flags missing clauses, unclear pricing, and operational friction.</p>
            </div>
            <div className="metric-card p-4">
              <p className="text-sm text-[color:var(--muted)]">Next action</p>
              <p className="mt-2 text-lg font-semibold">Recommends whether to buy, escalate, or reject.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
