import Stripe from "stripe";

import type { BillingEventLog } from "@/lib/billing-log";

function extractPlanFromMetadata(metadata: Record<string, string> | null | undefined, fallback: string) {
  return metadata?.plan || fallback;
}

export function buildBillingEventLog(event: Stripe.Event): BillingEventLog {
  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      return {
        stripeEventId: event.id,
        stripeEventType: event.type,
        plan: extractPlanFromMetadata(session.metadata, session.mode || "unknown"),
        accessState: "active",
        userId: session.metadata?.userId || null,
        customerEmail: session.customer_details?.email || null,
        customerId: typeof session.customer === "string" ? session.customer : null,
        createdAt: new Date().toISOString(),
      };
    }
    case "invoice.payment_succeeded": {
      const invoice = event.data.object as Stripe.Invoice;
      return {
        stripeEventId: event.id,
        stripeEventType: event.type,
          plan: extractPlanFromMetadata(invoice.subscription_details?.metadata, "pro"),
        accessState: "payment_received",
          userId: invoice.subscription_details?.metadata?.userId || null,
        customerEmail: invoice.customer_email || null,
        customerId: typeof invoice.customer === "string" ? invoice.customer : null,
        createdAt: new Date().toISOString(),
      };
    }
    case "customer.subscription.deleted": {
      const subscription = event.data.object as Stripe.Subscription;
      return {
        stripeEventId: event.id,
        stripeEventType: event.type,
        plan: extractPlanFromMetadata(subscription.metadata, subscription.items.data[0]?.price?.type || "pro"),
        accessState: "canceled",
        userId: subscription.metadata?.userId || null,
        customerEmail: null,
        customerId: typeof subscription.customer === "string" ? subscription.customer : null,
        createdAt: new Date().toISOString(),
      };
    }
    default:
      return {
        stripeEventId: event.id,
        stripeEventType: event.type,
        plan: "n/a",
        accessState: "ignored",
        userId: null,
        customerEmail: null,
        customerId: null,
        createdAt: new Date().toISOString(),
      };
  }
}
