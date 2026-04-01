import Link from "next/link";

import { PageViewTracker } from "@/components/page-view-tracker";
import { SiteHeader } from "@/components/site-header";

type SuccessPageProps = {
  searchParams: Promise<{
    plan?: string;
  }>;
};

export default async function SuccessPage({ searchParams }: SuccessPageProps) {
  const params = await searchParams;
  const plan = params.plan || "pro";

  return (
    <main className="pb-16">
      <PageViewTracker eventName="page_view_success" metadata={{ plan }} />
      <SiteHeader />
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10 lg:px-10">
        <div className="panel p-8 lg:p-10">
          <span className="headline-badge">Payment received</span>
          <h1 className="mt-4 text-5xl tracking-[-0.04em]">Checkout completed for {plan}.</h1>
          <p className="mt-5 text-lg leading-8 text-[color:var(--muted)]">
            This page confirms the payment flow is wired. The next implementation milestone is syncing access rights with a user profile and history.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row">
            <Link href="/upload" className="cta-primary">
              Analyze next PDF
            </Link>
            <Link href="/onboarding" className="cta-secondary">
              Open onboarding
            </Link>
            <Link href="/pricing" className="cta-secondary">
              Back to pricing
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
