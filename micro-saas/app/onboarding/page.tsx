import Link from "next/link";

import { SiteHeader } from "@/components/site-header";

const steps = [
  "Upload your first real PDF from target workflow.",
  "Review verdict and share summary with one stakeholder.",
  "Run a second document and compare decision confidence.",
  "If value is clear, continue with Pro or Founding plan.",
];

export default function OnboardingPage() {
  return (
    <main className="pb-16">
      <SiteHeader />
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-8 lg:px-10 lg:py-10">
        <div>
          <span className="headline-badge">Onboarding</span>
          <h1 className="mt-4 text-5xl tracking-[-0.04em]">First-week activation checklist</h1>
          <p className="mt-4 max-w-3xl text-lg leading-8 text-[color:var(--muted)]">
            Keep this flow simple: prove value in the first three documents, then iterate pricing and automation.
          </p>
        </div>

        <ol className="grid gap-4">
          {steps.map((step) => (
            <li key={step} className="panel p-5 text-base leading-7">
              {step}
            </li>
          ))}
        </ol>

        <div className="flex flex-col gap-4 sm:flex-row">
          <Link href="/upload" className="cta-primary">
            Analyze now
          </Link>
          <Link href="/account" className="cta-secondary">
            Open account
          </Link>
        </div>
      </section>
    </main>
  );
}
