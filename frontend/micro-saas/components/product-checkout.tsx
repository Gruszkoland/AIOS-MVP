"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

// T=0.8 - BoosterLever: High Performance Checkout Component
// ADRION 369 v2.0 - Lead Logic: Convert Single Sale to Checkout

interface ProductCheckoutProps {
  sku: string;
  name: string;
  price: number;
}

export function ProductCheckout({ sku, name, price }: ProductCheckoutProps) {
  const [loading, setLoading] = useState(false);
  const [vortexState, setVortexState] = useState<any>(null);
  const router = useRouter();

  const handleCheckout = async () => {
    setLoading(true);
    try {
      // Trinity-Log: Intellectual Layer scan before Material action
      const vortexApi =
        process.env.NEXT_PUBLIC_VORTEX_API || "http://localhost:1740";
      const checkResonance = await fetch(`${vortexApi}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          price_a: price,
          price_b: price * 0.85, // Example internal comparison
          channel: "AUDIO_PREMIUM",
        }),
      }).catch(() => null);

      if (checkResonance) {
        const resonance = await checkResonance.json();
        setVortexState(resonance);
        console.log("ADRION 369 Vortex Resonance:", resonance);
      }

      // Proceed to Stripe checkout
      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: "pro",
          metadata: {
            sku,
            product_name: name,
            type: "single_deal_lead",
          },
        }),
      });

      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        console.error("No checkout URL returned");
      }
    } catch (err) {
      console.error("Checkout failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {vortexState && (
        <div className="text-xs font-mono text-center p-2 border border-black/10 rounded flex items-center justify-center gap-2 animate-pulse">
          <span className="w-2 h-2 rounded-full bg-blue-500"></span>
          RESONANCE: {vortexState.resonance} | FREQ: {vortexState.frequency}Hz |{" "}
          {vortexState.message}
        </div>
      )}
      <button
        onClick={handleCheckout}
        disabled={loading}
        className="w-full py-4 bg-black text-white text-xl font-black rounded-lg hover:bg-gray-800 transition-all transform hover:scale-[1.02] disabled:bg-gray-400 disabled:scale-100"
      >
        {loading ? "PRZETWARZANIE..." : "ODBLOKUJ OFERTĘ (STRIPE)"}
      </button>
    </div>
  );
}
