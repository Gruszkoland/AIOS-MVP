import { NextResponse } from "next/server";

import { appendFunnelEvent, readFunnelEventsForUser, type FunnelEventName } from "@/lib/funnel-events";

export const runtime = "nodejs";

type FunnelEventBody = {
  name?: FunnelEventName;
  metadata?: Record<string, string | number | boolean | null>;
};

export async function POST(request: Request) {
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const body = (await request.json().catch(() => ({}))) as FunnelEventBody;

  if (!body.name) {
    return NextResponse.json({ error: "Missing funnel event name." }, { status: 400 });
  }

  const entry = await appendFunnelEvent({
    userId,
    name: body.name,
    metadata: body.metadata || {},
  });

  return NextResponse.json({ ok: true, entry }, { status: 200 });
}

export async function GET(request: Request) {
  const userId = request.headers.get("x-user-id")?.trim() || "anonymous";
  const url = new URL(request.url);
  const limitParam = Number(url.searchParams.get("limit") || "50");
  const limit = Number.isFinite(limitParam) ? Math.max(1, Math.min(200, limitParam)) : 50;
  const events = await readFunnelEventsForUser(userId, limit);

  return NextResponse.json(
    {
      userId,
      count: events.length,
      events,
    },
    { status: 200 },
  );
}
