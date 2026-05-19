import Link from "next/link";

import { HistoryList } from "@/components/history-list";
import { SiteHeader } from "@/components/site-header";

export default function HistoryPage() {
  return (
    <main className="pb-16">
      <SiteHeader />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:px-10 lg:py-10">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="headline-badge">Analysis history</span>
            <h1 className="mt-4 text-5xl tracking-[-0.04em]">Your analyses and parser outcomes.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-[color:var(--muted)]">
              This view is scoped to your local user id. Entries are written to runtime logs for MVP validation and can be replaced with database persistence later.
            </p>
          </div>
          <Link href="/upload" className="cta-secondary">
            Analyze new PDF
          </Link>
        </div>
        <HistoryList />
      </section>
    </main>
  );
}
