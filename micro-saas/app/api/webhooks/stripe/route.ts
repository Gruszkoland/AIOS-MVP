import { headers } from "next/headers";
import { NextResponse } from "next/server";
import Stripe from "stripe";

import { buildBillingEventLog } from "@/lib/billing-events";
import { appendBillingEvent } from "@/lib/billing-log";
import { appendEntitlementEntry } from "@/lib/entitlements";
import { appendFunnelEvent } from "@/lib/funnel-events";

export const runtime = "nodejs";

const HANDLED_EVENT_TYPES = new Set([
  "checkout.session.completed",
  "invoice.payment_succeeded",
  "customer.subscription.deleted",
]);

export async function POST(request: Request) {
  const secretKey = process.env.STRIPE_SECRET_KEY;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!secretKey || !webhookSecret) {
    return NextResponse.json(
      { error: "Stripe webhook is not configured. Add STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET." },
      { status: 503 },
    );
  }

  const stripe = new Stripe(secretKey, {
    apiVersion: "2025-02-24.acacia",
  });

  const signature = (await headers()).get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "Missing Stripe signature header." }, { status: 400 });
  }

  const rawBody = await request.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, webhookSecret);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Invalid webhook signature.";
    return NextResponse.json({ error: message }, { status: 400 });
  }

  const billingEvent = buildBillingEventLog(event);
  const logPath = await appendBillingEvent(billingEvent);

  if (billingEvent.userId && billingEvent.accessState !== "ignored") {
    await appendEntitlementEntry({
      userId: billingEvent.userId,
      plan: billingEvent.plan === "founding" ? "founding" : billingEvent.plan === "pro" ? "pro" : "free",
      source: "stripe-webhook",
      eventType: billingEvent.stripeEventType,
      accessState: billingEvent.accessState,
      createdAt: new Date().toISOString(),
    });

    if (billingEvent.stripeEventType === "checkout.session.completed") {
      await appendFunnelEvent({
        userId: billingEvent.userId,
        name: "checkout_success",
        metadata: {
          plan: billingEvent.plan,
        },
      });
    }

    if (billingEvent.stripeEventType === "customer.subscription.deleted") {
      await appendFunnelEvent({
        userId: billingEvent.userId,
        name: "subscription_canceled",
        metadata: {
          plan: billingEvent.plan,
        },
      });
    }
  }

  return NextResponse.json(
    {
      received: true,
      handled: HANDLED_EVENT_TYPES.has(event.type),
      eventType: event.type,
      accessState: billingEvent.accessState,
      plan: billingEvent.plan,
      logPath,
    },
    { status: 200 },
  );
}
