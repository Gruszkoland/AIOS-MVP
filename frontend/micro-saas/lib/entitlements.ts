import { appendFile, mkdir, readFile } from "node:fs/promises";
import path from "node:path";

export type PlanTier = "free" | "pro" | "founding";

export type EntitlementEntry = {
  userId: string;
  plan: PlanTier;
  source: "stripe-webhook" | "manual";
  eventType: string;
  accessState: "active" | "canceled" | "payment_received" | "ignored";
  createdAt: string;
};

function getRuntimeDir() {
  return path.join(process.cwd(), ".runtime");
}

function getEntitlementsPath() {
  return path.join(getRuntimeDir(), "entitlements.log");
}

function normalizePlan(plan: string): PlanTier {
  if (plan === "pro") {
    return "pro";
  }
  if (plan === "founding") {
    return "founding";
  }
  return "free";
}

export async function appendEntitlementEntry(entry: EntitlementEntry) {
  await mkdir(getRuntimeDir(), { recursive: true });
  await appendFile(getEntitlementsPath(), `${JSON.stringify(entry)}\n`, "utf8");
}

export async function readEntitlements(limit = 200) {
  try {
    const content = await readFile(getEntitlementsPath(), "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-limit)
      .map((line) => JSON.parse(line) as EntitlementEntry);
  } catch {
    return [] as EntitlementEntry[];
  }
}

export async function resolvePlanTier(userId: string): Promise<PlanTier> {
  const entries = await readEntitlements(500);
  const userEntries = entries.filter((entry) => entry.userId === userId);

  if (userEntries.length === 0) {
    return "free";
  }

  const latest = userEntries[userEntries.length - 1];
  if (latest.accessState === "canceled") {
    return "free";
  }

  return normalizePlan(latest.plan);
}
