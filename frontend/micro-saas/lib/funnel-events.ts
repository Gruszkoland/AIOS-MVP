import { appendFile, mkdir, readFile } from "node:fs/promises";
import path from "node:path";

export type FunnelEventName =
  | "page_view_home"
  | "page_view_upload"
  | "page_view_pricing"
  | "page_view_success"
  | "analysis_submit"
  | "analysis_success"
  | "analysis_error"
  | "checkout_start"
  | "checkout_error"
  | "checkout_success"
  | "subscription_canceled";

export type FunnelEvent = {
  id: string;
  userId: string;
  name: FunnelEventName;
  metadata: Record<string, string | number | boolean | null>;
  createdAt: string;
};

function getRuntimeDir() {
  return path.join(process.cwd(), ".runtime");
}

function getFunnelPath() {
  return path.join(getRuntimeDir(), "funnel-events.log");
}

export async function appendFunnelEvent(event: Omit<FunnelEvent, "id" | "createdAt">) {
  const entry: FunnelEvent = {
    id: `funnel-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    createdAt: new Date().toISOString(),
    ...event,
  };

  await mkdir(getRuntimeDir(), { recursive: true });
  await appendFile(getFunnelPath(), `${JSON.stringify(entry)}\n`, "utf8");
  return entry;
}

export async function readFunnelEventsForUser(userId: string, limit = 50) {
  try {
    const content = await readFile(getFunnelPath(), "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line) as FunnelEvent)
      .filter((event) => event.userId === userId)
      .slice(-limit)
      .reverse();
  } catch {
    return [] as FunnelEvent[];
  }
}

export async function readAllFunnelEvents(limit = 1000) {
  try {
    const content = await readFile(getFunnelPath(), "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-limit)
      .map((line) => JSON.parse(line) as FunnelEvent);
  } catch {
    return [] as FunnelEvent[];
  }
}

export async function readAllFunnelEventsForUser(userId: string) {
  try {
    const content = await readFile(getFunnelPath(), "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line) as FunnelEvent)
      .filter((event) => event.userId === userId);
  } catch {
    return [] as FunnelEvent[];
  }
}
