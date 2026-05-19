import { appendFile, mkdir, readFile } from "node:fs/promises";
import path from "node:path";

import type { AnalysisResult } from "@/lib/mock-analysis";

export type AnalysisHistoryEntry = {
  id: string;
  createdAt: string;
  userId: string;
  result: AnalysisResult;
};

function getRuntimeDir() {
  return path.join(process.cwd(), ".runtime");
}

function getHistoryPath() {
  return path.join(getRuntimeDir(), "analysis-history.log");
}

export async function appendAnalysisHistory(result: AnalysisResult, userId: string) {
  const entry: AnalysisHistoryEntry = {
    id: result.id,
    createdAt: new Date().toISOString(),
    userId,
    result,
  };

  const runtimeDir = getRuntimeDir();
  await mkdir(runtimeDir, { recursive: true });
  await appendFile(getHistoryPath(), `${JSON.stringify(entry)}\n`, "utf8");

  return entry;
}

export async function readAnalysisHistory(limit = 20) {
  try {
    const content = await readFile(getHistoryPath(), "utf8");
    return content
      .split(/\r?\n/)
      .filter(Boolean)
      .slice(-limit)
      .map((line) => JSON.parse(line) as AnalysisHistoryEntry)
      .reverse();
  } catch {
    return [] as AnalysisHistoryEntry[];
  }
}

export async function readAnalysisHistoryForUser(userId: string, limit = 20) {
  const entries = await readAnalysisHistory(500);
  return entries.filter((entry) => entry.userId === userId).slice(0, limit);
}

export async function countAnalysesForUserOnDate(userId: string, isoDate: string) {
  const entries = await readAnalysisHistory(500);
  return entries.filter((entry) => entry.userId === userId && entry.createdAt.slice(0, 10) === isoDate).length;
}
