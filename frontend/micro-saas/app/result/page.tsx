import Link from "next/link";

import { AnalysisPreview } from "@/components/analysis-preview";
import { SiteHeader } from "@/components/site-header";
import { decodePayload } from "@/lib/mock-analysis";

type ResultPageProps = {
  searchParams: Promise<{
    payload?: string;
  }>;
};

export default async function ResultPage({ searchParams }: ResultPageProps) {
  const params = await searchParams;
  const result = decodePayload(params.payload);

  return (
    <main className="pb-16">
      <SiteHeader />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:px-10 lg:py-10">
        {result ? (
          <AnalysisPreview result={result} />
        ) : (
          <div className="panel flex flex-col items-start gap-5 p-8">
            <span className="headline-badge">No result yet</span>
            <h1 className="text-4xl tracking-[-0.04em]">The result page is ready, but you have not run an analysis yet.</h1>
            <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted)]">
              Start with the upload flow so the route can build a mock decision package and route it here.
            </p>
            <Link href="/upload" className="cta-primary">
              Go to upload
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}
