import { readAnalysisHistory } from "@/lib/analysis-history";
import { readBillingEvents } from "@/lib/billing-log";
import { readAllFunnelEvents } from "@/lib/funnel-events";

type DailyReportSnapshot = {
  generatedAt: string;
  uniqueUsers24h: number;
  analyses24h: number;
  parseReal24h: number;
  parseMock24h: number;
  checkoutStarts24h: number;
  checkoutSuccesses24h: number;
  subscriptionCanceled24h: number;
  conversionRate24h: number;
  billingActive24h: number;
  billingCanceled24h: number;
  billingPaymentReceived24h: number;
};

function isInLast24h(iso: string) {
  const now = Date.now();
  const ts = new Date(iso).getTime();
  return Number.isFinite(ts) && now - ts <= 24 * 60 * 60 * 1000;
}

function asRate(numerator: number, denominator: number) {
  if (denominator <= 0) {
    return 0;
  }
  return Math.round((numerator / denominator) * 10000) / 100;
}

export async function buildDailyReportSnapshot(): Promise<DailyReportSnapshot> {
  const [analyses, billing, funnel] = await Promise.all([
    readAnalysisHistory(2000),
    readBillingEvents(2000),
    readAllFunnelEvents(4000),
  ]);

  const analyses24h = analyses.filter((entry) => isInLast24h(entry.createdAt));
  const billing24h = billing.filter((entry) => isInLast24h(entry.createdAt));
  const funnel24h = funnel.filter((entry) => isInLast24h(entry.createdAt));

  const uniqueUsers = new Set<string>();
  for (const event of funnel24h) {
    if (event.userId) {
      uniqueUsers.add(event.userId);
    }
  }

  const checkoutStarts24h = funnel24h.filter((event) => event.name === "checkout_start").length;
  const checkoutSuccesses24h = funnel24h.filter((event) => event.name === "checkout_success").length;
  const subscriptionCanceled24h = funnel24h.filter((event) => event.name === "subscription_canceled").length;

  return {
    generatedAt: new Date().toISOString(),
    uniqueUsers24h: uniqueUsers.size,
    analyses24h: analyses24h.length,
    parseReal24h: analyses24h.filter((entry) => entry.result.parseMode === "real").length,
    parseMock24h: analyses24h.filter((entry) => entry.result.parseMode !== "real").length,
    checkoutStarts24h,
    checkoutSuccesses24h,
    subscriptionCanceled24h,
    conversionRate24h: asRate(checkoutSuccesses24h, checkoutStarts24h),
    billingActive24h: billing24h.filter((entry) => entry.accessState === "active").length,
    billingCanceled24h: billing24h.filter((entry) => entry.accessState === "canceled").length,
    billingPaymentReceived24h: billing24h.filter((entry) => entry.accessState === "payment_received").length,
  };
}

export function renderDailyReportHtml(snapshot: DailyReportSnapshot) {
  return `
    <div style="font-family:Segoe UI,Arial,sans-serif;line-height:1.6;color:#1b1b1b;max-width:680px;margin:0 auto;padding:24px;">
      <h2 style="margin:0 0 8px 0;">Daily SaaS Report (09:00)</h2>
      <p style="margin:0 0 16px 0;color:#666;">Generated: ${snapshot.generatedAt}</p>
      <table style="width:100%;border-collapse:collapse;">
        <tbody>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Unique users (24h)</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.uniqueUsers24h}</strong></td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Analyses (24h)</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.analyses24h}</strong></td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Real parser / Mock parser</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.parseReal24h} / ${snapshot.parseMock24h}</strong></td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Checkout starts / successes</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.checkoutStarts24h} / ${snapshot.checkoutSuccesses24h}</strong></td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Checkout conversion (24h)</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.conversionRate24h}%</strong></td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Subscription canceled (24h)</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.subscriptionCanceled24h}</strong></td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #ececec;">Billing active / payment / canceled</td><td style="padding:8px;border-bottom:1px solid #ececec;text-align:right;"><strong>${snapshot.billingActive24h} / ${snapshot.billingPaymentReceived24h} / ${snapshot.billingCanceled24h}</strong></td></tr>
        </tbody>
      </table>
    </div>
  `;
}

export type { DailyReportSnapshot };
