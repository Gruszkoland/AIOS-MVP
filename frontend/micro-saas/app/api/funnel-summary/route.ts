import { NextResponse } from "next/server";

import { buildFunnelSummaryForUser } from "@/lib/funnel-summary";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const summary = await buildFunnelSummaryForUser(userId);

  return NextResponse.json(
    {
      userId,
      summary,
    },
    { status: 200 },
  );
}
