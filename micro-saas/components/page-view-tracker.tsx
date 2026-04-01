"use client";

import { useEffect } from "react";

import { trackFunnelEvent } from "@/lib/funnel-client";

type PageViewTrackerProps = {
  eventName: "page_view_home" | "page_view_upload" | "page_view_pricing" | "page_view_success";
  metadata?: Record<string, string | number | boolean | null>;
};

export function PageViewTracker({ eventName, metadata = {} }: PageViewTrackerProps) {
  useEffect(() => {
    void trackFunnelEvent(eventName, metadata);
  }, [eventName, metadata]);

  return null;
}
