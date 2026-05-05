import { NextResponse } from "next/server";

import { readBillingEventsForUser } from "@/lib/billing-log";
import { buildFunnelSummaryForUser } from "@/lib/funnel-summary";

export const runtime = "nodejs";

function toCsvRow(values: Array<string | number>) {
  return values
    .map((value) => String(value).replace(/"/g, '""'))
    .map((value) => `"${value}"`)
    .join(",");
}

export async function GET(request: Request) {
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const url = new URL(request.url);
  const format = (url.searchParams.get("format") || "json").toLowerCase();

  const summary = await buildFunnelSummaryForUser(userId);
  const billingEvents = await readBillingEventsForUser(userId, 20);

  if (format === "csv") {
    const lines: string[] = [];
    lines.push(toCsvRow(["section", "metric", "value"]));
    lines.push(toCsvRow(["funnel", "homeViews", summary.homeViews]));
    lines.push(toCsvRow(["funnel", "uploadViews", summary.uploadViews]));
    lines.push(toCsvRow(["funnel", "pricingViews", summary.pricingViews]));
    lines.push(toCsvRow(["funnel", "analysisSubmits", summary.analysisSubmits]));
    lines.push(toCsvRow(["funnel", "analysisSuccesses", summary.analysisSuccesses]));
    lines.push(toCsvRow(["funnel", "checkoutStarts", summary.checkoutStarts]));
    lines.push(toCsvRow(["funnel", "checkoutSuccesses", summary.checkoutSuccesses]));
    lines.push(toCsvRow(["funnel", "analysisSuccessRate", summary.analysisSuccessRate]));
    lines.push(toCsvRow(["funnel", "checkoutConversionRate", summary.checkoutConversionRate]));

    for (const event of billingEvents) {
      lines.push(toCsvRow(["billing", event.stripeEventType, `${event.accessState}:${event.plan}`]));
    }

    return new NextResponse(lines.join("\n"), {
      status: 200,
      headers: {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": `attachment; filename="funnel-report-${userId}.csv"`,
      },
    });
  }

  return NextResponse.json(
    {
      userId,
      generatedAt: new Date().toISOString(),
      funnel: summary,
      recentBillingEvents: billingEvents,
    },
    {
      status: 200,
      headers: {
        "Content-Disposition": `attachment; filename="funnel-report-${userId}.json"`,
      },
    },
  );
}
