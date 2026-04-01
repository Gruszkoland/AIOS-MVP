import Link from "next/link";

import { AccountOverview } from "@/components/account-overview";
import { SiteHeader } from "@/components/site-header";

export default function AccountPage() {
  return (
    <main className="pb-16">
      <SiteHeader />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:px-10 lg:py-10">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="headline-badge">Account</span>
            <h1 className="mt-4 text-5xl tracking-[-0.04em]">Plan, usage, and billing status in one place.</h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-[color:var(--muted)]">
              This dashboard is user-scoped and powered by local runtime logs. It is the MVP bridge before full database-backed account management.
            </p>
          </div>
          <Link href="/upload" className="cta-secondary">
            Analyze new PDF
          </Link>
        </div>

        <AccountOverview />
      </section>
    </main>
  );
}
