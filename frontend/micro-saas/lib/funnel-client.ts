"use client";

import { getOrCreateUserId } from "@/lib/client-user-id";

type FunnelClientEventName =
  | "page_view_home"
  | "page_view_upload"
  | "page_view_pricing"
  | "page_view_success"
  | "analysis_submit"
  | "analysis_success"
  | "analysis_error"
  | "checkout_start"
  | "checkout_error";

export async function trackFunnelEvent(
  name: FunnelClientEventName,
  metadata: Record<string, string | number | boolean | null> = {},
) {
  const userId = getOrCreateUserId();

  try {
    await fetch("/api/funnel-events", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-user-id": userId,
      },
      body: JSON.stringify({
        name,
        metadata,
      }),
    });
  } catch {
    // Analytics in MVP should not block product flow.
  }
}
