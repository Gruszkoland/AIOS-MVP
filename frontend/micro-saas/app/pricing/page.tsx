import Link from "next/link";

import { PageViewTracker } from "@/components/page-view-tracker";
import { PricingCards } from "@/components/pricing-cards";
import { SiteHeader } from "@/components/site-header";

type PricingPageProps = {
  searchParams: Promise<{
    canceled?: string;
  }>;
};

export default async function PricingPage({ searchParams }: PricingPageProps) {
  const params = await searchParams;
  const isCanceled = params.canceled === "1";

  return (
    <main className="pb-16">
      <PageViewTracker eventName="page_view_pricing" metadata={{ canceled: isCanceled }} />
      <SiteHeader />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:px-10 lg:py-10">
        {isCanceled ? (
          <div className="rounded-3xl border border-amber-300 bg-amber-50 px-5 py-4 text-sm text-amber-900">
            Checkout was canceled. Your plan has not changed, and you can retry safely.
          </div>
        ) : null}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="headline-badge">Pricing placeholder</span>
            <h1 className="mt-4 text-5xl tracking-[-0.04em]">One clear offer beats a complex billing matrix at this stage.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-[color:var(--muted)]">
              Keep pricing simple until you confirm that the analysis actually saves time or reduces decision risk for a paying customer.
            </p>
          </div>
          <Link href="/upload" className="cta-secondary">
            Return to upload
          </Link>
        </div>
        <PricingCards />
      </section>
    </main>
  );
}
