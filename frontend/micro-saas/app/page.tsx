import Link from "next/link";

import { HeroSection } from "@/components/hero-section";
import { PageViewTracker } from "@/components/page-view-tracker";
import { SiteHeader } from "@/components/site-header";

const steps = [
  {
    title: "Upload a document",
    description: "Start with one PDF from a real workflow. This keeps the first MVP honest and measurable.",
  },
  {
    title: "Get a decision summary",
    description: "The server mock returns the exact shape you need for a future AI or extraction backend.",
  },
  {
    title: "Upsell premium action",
    description: "The next monetization step is gating export, repeat usage, or saved workspaces behind billing.",
  },
];

export default function HomePage() {
  return (
    <main className="pb-16">
      <PageViewTracker eventName="page_view_home" />
      <SiteHeader />
      <HeroSection />

      <section className="mx-auto grid w-full max-w-6xl gap-6 px-6 lg:grid-cols-3 lg:px-10">
        {steps.map((step, index) => (
          <article key={step.title} className="panel p-6 lg:p-8">
            <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Step 0{index + 1}</p>
            <h2 className="mt-3 text-2xl tracking-[-0.03em]">{step.title}</h2>
            <p className="mt-4 text-base leading-7 text-[color:var(--muted)]">{step.description}</p>
          </article>
        ))}
      </section>

      <section className="mx-auto mt-10 flex w-full max-w-6xl flex-col gap-5 px-6 lg:flex-row lg:items-center lg:justify-between lg:px-10">
        <div>
          <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">Build target</p>
          <h2 className="mt-2 text-3xl tracking-[-0.03em]">The first implementation is flow-first, not infra-first.</h2>
        </div>
        <Link href="/upload" className="cta-primary">
          Open MVP upload
        </Link>
      </section>
    </main>
  );
}
