import { readAllFunnelEventsForUser } from "@/lib/funnel-events";

export type FunnelSummary = {
  homeViews: number;
  uploadViews: number;
  pricingViews: number;
  analysisSubmits: number;
  analysisSuccesses: number;
  checkoutStarts: number;
  checkoutSuccesses: number;
  analysisSuccessRate: number;
  checkoutConversionRate: number;
};

function countByName(events: Array<{ name: string }>, name: string) {
  return events.filter((event) => event.name === name).length;
}

function asRate(numerator: number, denominator: number) {
  if (denominator <= 0) {
    return 0;
  }
  return Math.round((numerator / denominator) * 10000) / 100;
}

export async function buildFunnelSummaryForUser(userId: string): Promise<FunnelSummary> {
  const events = await readAllFunnelEventsForUser(userId);

  const homeViews = countByName(events, "page_view_home");
  const uploadViews = countByName(events, "page_view_upload");
  const pricingViews = countByName(events, "page_view_pricing");
  const analysisSubmits = countByName(events, "analysis_submit");
  const analysisSuccesses = countByName(events, "analysis_success");
  const checkoutStarts = countByName(events, "checkout_start");
  const checkoutSuccesses = countByName(events, "checkout_success");

  return {
    homeViews,
    uploadViews,
    pricingViews,
    analysisSubmits,
    analysisSuccesses,
    checkoutStarts,
    checkoutSuccesses,
    analysisSuccessRate: asRate(analysisSuccesses, analysisSubmits),
    checkoutConversionRate: asRate(checkoutSuccesses, checkoutStarts),
  };
}
