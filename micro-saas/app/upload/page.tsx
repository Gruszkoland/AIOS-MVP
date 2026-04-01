import { PageViewTracker } from "@/components/page-view-tracker";
import { SiteHeader } from "@/components/site-header";
import { UploadForm } from "@/components/upload-form";

export default function UploadPage() {
  return (
    <main className="pb-16">
      <PageViewTracker eventName="page_view_upload" />
      <SiteHeader />
      <section className="mx-auto grid w-full max-w-6xl gap-8 px-6 py-8 lg:grid-cols-[0.85fr_1.15fr] lg:px-10 lg:py-10">
        <div className="space-y-5">
          <span className="headline-badge">MVP upload step</span>
          <h1 className="text-5xl leading-[0.96] tracking-[-0.04em]">Test the upload and result loop before adding real AI costs.</h1>
          <p className="text-lg leading-8 text-[color:var(--muted)]">
            This step validates the habit-forming part of the product: user intent, file handoff, server response, and a premium call to action.
          </p>
          <div className="metric-card p-5">
            <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">What is mocked</p>
            <p className="mt-3 text-base leading-7">
              PDF extraction, embeddings, clause parsing, and billing are intentionally deferred. The payload shape is ready for a real backend later.
            </p>
          </div>
        </div>
        <UploadForm />
      </section>
    </main>
  );
}
