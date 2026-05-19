import { NextResponse } from "next/server";
import Stripe from "stripe";

export const runtime = "nodejs";

type CheckoutBody = {
  plan?: "pro" | "founding";
  userId?: string;
};

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as CheckoutBody;
  const requestedPlan = body.plan || "pro";
  const userId = typeof body.userId === "string" && body.userId.trim().length > 0 ? body.userId.trim() : null;

  if (requestedPlan !== "pro" && requestedPlan !== "founding") {
    return NextResponse.json({ error: "Unsupported plan selected." }, { status: 400 });
  }

  const secretKey = process.env.STRIPE_SECRET_KEY;
  const appUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  const monthlyPriceId = process.env.STRIPE_PRICE_ID_PRO;
  const foundingPriceId = process.env.STRIPE_PRICE_ID_FOUNDING;

  const selectedPriceId = requestedPlan === "pro" ? monthlyPriceId : foundingPriceId;

  if (!secretKey || !selectedPriceId) {
    return NextResponse.json(
      {
        error: "Stripe is not configured yet. Add STRIPE_SECRET_KEY and plan price IDs in .env.local.",
      },
      { status: 503 },
    );
  }

  const stripe = new Stripe(secretKey, {
    apiVersion: "2025-02-24.acacia",
  });

  const session = await stripe.checkout.sessions.create({
    mode: requestedPlan === "pro" ? "subscription" : "payment",
    line_items: [{ price: selectedPriceId, quantity: 1 }],
    success_url: `${appUrl}/success?plan=${requestedPlan}`,
    cancel_url: `${appUrl}/pricing?canceled=1`,
    metadata: {
      source: "micro-saas-mvp",
      plan: requestedPlan,
      userId: userId || "anonymous",
    },
    client_reference_id: userId || undefined,
  });

  return NextResponse.json({ url: session.url }, { status: 200 });
}
