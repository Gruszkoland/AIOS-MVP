import { mkdir, appendFile, readFile } from "node:fs/promises";
import path from "node:path";

export type BillingEventLog = {
  stripeEventId: string;
  stripeEventType: string;
  plan: string;
  accessState: "active" | "canceled" | "payment_received" | "ignored";
  userId: string | null;
  customerEmail: string | null;
  customerId: string | null;
  createdAt: string;
};

function getRuntimeDir() {
  return path.join(process.cwd(), ".runtime");
}

export async function appendBillingEvent(event: BillingEventLog) {
  const runtimeDir = getRuntimeDir();
  const logPath = path.join(runtimeDir, "stripe-events.log");

  await mkdir(runtimeDir, { recursive: true });
  await appendFile(logPath, `${JSON.stringify(event)}\n`, "utf8");

  return logPath;
}

export async function readBillingEvents(limit = 20) {
  const logPath = path.join(getRuntimeDir(), "stripe-events.log");

  try {
    const content = await readFile(logPath, "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-limit)
      .map((line) => JSON.parse(line) as BillingEventLog)
      .reverse();
  } catch {
    return [] as BillingEventLog[];
  }
}

export async function readBillingEventsForUser(userId: string, limit = 20) {
  const events = await readBillingEvents(500);
  return events.filter((event) => event.userId === userId).slice(0, limit);
}
