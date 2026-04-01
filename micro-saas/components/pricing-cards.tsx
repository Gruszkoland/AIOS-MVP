"use client";

import { useState } from "react";

import { getOrCreateUserId } from "@/lib/client-user-id";
import { trackFunnelEvent } from "@/lib/funnel-client";

const plans = [
  {
    name: "Free",
    price: "0 zl",
    description: "Validate the flow and one daily document.",
    features: ["1 PDF per day", "Summary and verdict", "No export"],
    highlight: false,
    checkoutPlan: null,
  },
  {
    name: "Pro",
    price: "79 zl / month",
    description: "For the first paid signal and repeat usage.",
    features: ["25 PDFs per month", "Risk matrix", "Decision memo export"],
    highlight: true,
    checkoutPlan: "pro",
  },
  {
    name: "Founding",
    price: "249 zl one-off",
    description: "Early adopter package for direct feedback loops.",
    features: ["90-day access", "Priority support", "Roadmap input"],
    highlight: false,
    checkoutPlan: "founding",
  },
] as const;

type PlanId = "pro" | "founding";

export function PricingCards() {
  const [isLoadingPlan, setIsLoadingPlan] = useState<PlanId | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function startCheckout(plan: PlanId) {
    setErrorMessage(null);
    setIsLoadingPlan(plan);
    void trackFunnelEvent("checkout_start", { plan });

    try {
      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          plan,
          userId: getOrCreateUserId(),
        }),
      });

      const payload = (await response.json().catch(() => null)) as { url?: string; error?: string } | null;

      if (!response.ok || !payload?.url) {
        throw new Error(payload?.error || "Checkout is unavailable right now.");
      }

      window.location.href = payload.url;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected checkout error.";
      setErrorMessage(message);
      setIsLoadingPlan(null);
      void trackFunnelEvent("checkout_error", {
        plan,
        message,
      });
    }
  }

  return (
    <div className="space-y-4">
      {errorMessage ? <p className="rounded-2xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">{errorMessage}</p> : null}
      <div className="grid gap-6 lg:grid-cols-3">
        {plans.map((plan) => (
          <article
            key={plan.name}
            className={`panel flex h-full flex-col gap-5 p-6 lg:p-8 ${plan.highlight ? "border-[color:var(--accent)] shadow-[0_20px_55px_rgba(138,44,22,0.15)]" : ""}`}
          >
            <div>
              <p className="text-sm uppercase tracking-[0.18em] text-[color:var(--muted)]">{plan.name}</p>
              <p className="mt-3 text-4xl tracking-[-0.04em]">{plan.price}</p>
              <p className="mt-3 text-base leading-7 text-[color:var(--muted)]">{plan.description}</p>
            </div>
            <ul className="space-y-3 text-sm leading-6">
              {plan.features.map((feature) => (
                <li key={feature} className="rounded-2xl border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
                  {feature}
                </li>
              ))}
            </ul>
            {plan.checkoutPlan ? (
              <button
                onClick={() => startCheckout(plan.checkoutPlan)}
                disabled={isLoadingPlan !== null}
                className={`mt-auto rounded-full px-5 py-3 text-sm font-bold ${plan.highlight ? "bg-[color:var(--accent)] text-white" : "border border-[color:var(--border)] bg-[color:var(--surface)]"} disabled:cursor-wait disabled:opacity-70`}
              >
                {isLoadingPlan === plan.checkoutPlan ? "Opening checkout..." : "Start checkout"}
              </button>
            ) : (
              <button className="mt-auto rounded-full border border-[color:var(--border)] bg-[color:var(--surface)] px-5 py-3 text-sm font-bold">
                Keep free plan
              </button>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
