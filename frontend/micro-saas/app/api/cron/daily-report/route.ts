import { NextResponse } from "next/server";
import { Resend } from "resend";

import { buildDailyReportSnapshot, renderDailyReportHtml } from "@/lib/daily-report";

export const runtime = "nodejs";

function isAuthorized(request: Request) {
  const configuredToken = process.env.DAILY_REPORT_TOKEN;
  if (!configuredToken) {
    return true;
  }

  const authHeader = request.headers.get("authorization");
  if (authHeader === `Bearer ${configuredToken}`) {
    return true;
  }

  const url = new URL(request.url);
  const tokenFromQuery = url.searchParams.get("token");
  return tokenFromQuery === configuredToken;
}

async function sendReportEmail() {
  const apiKey = process.env.RESEND_API_KEY;
  const to = process.env.DAILY_REPORT_TO || "punktodniesienia.adrian@gmail.com";
  const from = process.env.DAILY_REPORT_FROM || "SaaS Report <reports@resend.dev>";

  if (!apiKey) {
    return {
      sent: false,
      reason: "RESEND_API_KEY is missing.",
    };
  }

  const snapshot = await buildDailyReportSnapshot();
  const resend = new Resend(apiKey);

  const subjectDate = new Date(snapshot.generatedAt).toLocaleDateString("pl-PL");
  await resend.emails.send({
    from,
    to,
    subject: `Raport dzienny SaaS 09:00 - ${subjectDate}`,
    html: renderDailyReportHtml(snapshot),
  });

  return {
    sent: true,
    snapshot,
    to,
  };
}

export async function GET(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const result = await sendReportEmail();
  return NextResponse.json(result, { status: 200 });
}

export async function POST(request: Request) {
  return GET(request);
}
