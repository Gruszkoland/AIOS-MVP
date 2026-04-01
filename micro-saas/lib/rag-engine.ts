/**
 * ADRION 369 — Dynamic RAG Engine (PROGRAMATOR #13)
 *
 * Geo-localized market context for DE (DACH) vs PL arbitrage.
 * Provides market-specific data to product pages and analysis.
 *
 * Market Split:
 *   PL → "Najniższa Cena" (lowest price focus)
 *   DE → "Zertifizierter Händler" (certified dealer trust)
 *
 * Features:
 *   - getMarketContext(country) — context for hreflang/SEO
 *   - getProductContext(slug, country) — product-specific RAG
 *   - detectMarket(headers) — IP/header-based geo detection
 */

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export type MarketCode = "PL" | "DE" | "AT" | "CH";

export type MarketContext = {
  country: MarketCode;
  language: string;
  locale: string;
  currency: string;
  currencySymbol: string;
  trustSignal: string;
  pricingStrategy: string;
  hreflang: string;
  vatRate: number;
  shippingLabel: string;
  seoPrefix: string;
  metaDescription: string;
};

export type ProductRAGContext = {
  market: MarketContext;
  productSlug: string;
  pricingCopy: string;
  trustBadge: string;
  cta: string;
  urgencySignal: string;
  seoTitle: string;
  seoDescription: string;
  structuredData: Record<string, unknown>;
};

// ═══════════════════════════════════════════════════════════════
// MARKET DEFINITIONS
// ═══════════════════════════════════════════════════════════════

const MARKETS: Record<MarketCode, MarketContext> = {
  PL: {
    country: "PL",
    language: "pl",
    locale: "pl-PL",
    currency: "PLN",
    currencySymbol: "zł",
    trustSignal: "Najniższa Cena Gwarantowana",
    pricingStrategy: "lowest_price",
    hreflang: "pl",
    vatRate: 0.23,
    shippingLabel: "Darmowa dostawa od 200 zł",
    seoPrefix: "Kup",
    metaDescription:
      "Najlepsza cena {product} w Polsce. Bezpośrednio z magazynu centralnego DACH. Gwarancja producenta.",
  },
  DE: {
    country: "DE",
    language: "de",
    locale: "de-DE",
    currency: "EUR",
    currencySymbol: "€",
    trustSignal: "Zertifizierter Händler",
    pricingStrategy: "certified_dealer",
    hreflang: "de",
    vatRate: 0.19,
    shippingLabel: "Kostenloser Versand ab 50€",
    seoPrefix: "Kaufen",
    metaDescription:
      "Bester Preis für {product}. Direkt vom zertifizierten Händler. Herstellergarantie inklusive.",
  },
  AT: {
    country: "AT",
    language: "de",
    locale: "de-AT",
    currency: "EUR",
    currencySymbol: "€",
    trustSignal: "Zertifizierter Händler Österreich",
    pricingStrategy: "certified_dealer",
    hreflang: "de-AT",
    vatRate: 0.2,
    shippingLabel: "Kostenloser Versand nach Österreich",
    seoPrefix: "Kaufen",
    metaDescription:
      "Bester Preis für {product} in Österreich. Zertifizierter Händler mit Herstellergarantie.",
  },
  CH: {
    country: "CH",
    language: "de",
    locale: "de-CH",
    currency: "CHF",
    currencySymbol: "CHF",
    trustSignal: "Zertifizierter Schweizer Partner",
    pricingStrategy: "premium_trust",
    hreflang: "de-CH",
    vatRate: 0.077,
    shippingLabel: "Versandkostenfrei in die Schweiz",
    seoPrefix: "Kaufen",
    metaDescription:
      "Premium-Preis für {product} in der Schweiz. Schweizer Qualitätsgarantie.",
  },
};

// ═══════════════════════════════════════════════════════════════
// MARKET CONTEXT
// ═══════════════════════════════════════════════════════════════

/**
 * Get full market context for a country code.
 * Falls back to DE for unknown DACH countries, PL for others.
 */
export function getMarketContext(country: string): MarketContext {
  const code = country.toUpperCase() as MarketCode;
  if (code in MARKETS) {
    return MARKETS[code];
  }
  // DACH fallback
  if (["DE", "AT", "CH", "LI"].includes(code)) {
    return MARKETS.DE;
  }
  return MARKETS.PL;
}

// ═══════════════════════════════════════════════════════════════
// GEO DETECTION
// ═══════════════════════════════════════════════════════════════

/**
 * Detect market from request headers.
 * Checks: X-Vercel-IP-Country, CF-IPCountry, Accept-Language.
 */
export function detectMarket(headers: Record<string, string>): MarketContext {
  // Vercel / Cloudflare IP-based
  const ipCountry =
    headers["x-vercel-ip-country"] || headers["cf-ipcountry"] || "";
  if (ipCountry) {
    return getMarketContext(ipCountry);
  }

  // Accept-Language fallback
  const acceptLang = headers["accept-language"] || "";
  if (/^de/i.test(acceptLang)) return MARKETS.DE;
  if (/^pl/i.test(acceptLang)) return MARKETS.PL;

  // Default: PL (primary market)
  return MARKETS.PL;
}

// ═══════════════════════════════════════════════════════════════
// PRODUCT RAG CONTEXT
// ═══════════════════════════════════════════════════════════════

/**
 * Generate product-specific RAG context for a given market.
 * Used by product pages (app/products/[slug]/page.tsx) and SEO.
 */
export function getProductContext(
  slug: string,
  country: string,
  productData?: {
    name: string;
    retailPrice: number;
    wholesalePrice: number;
    stock: number;
  },
): ProductRAGContext {
  const market = getMarketContext(country);
  const name = productData?.name || slugToName(slug);
  const price = productData?.retailPrice || 0;
  const stock = productData?.stock || 0;

  // Market-specific pricing copy
  const pricingCopy =
    market.pricingStrategy === "lowest_price"
      ? `${market.seoPrefix} ${name} za ${formatPrice(price, market)} — najniższa cena w sieci`
      : `${market.seoPrefix} Sie ${name} für ${formatPrice(price, market)} — vom zertifizierten Händler`;

  // Trust badge
  const trustBadge = market.trustSignal;

  // CTA
  const cta =
    market.language === "pl"
      ? "Zamów teraz z gwarancją producenta"
      : "Jetzt bestellen mit Herstellergarantie";

  // Urgency signal
  let urgencySignal = "";
  if (stock > 0 && stock <= 5) {
    urgencySignal =
      market.language === "pl"
        ? `Ostatnie ${stock} sztuk w magazynie!`
        : `Nur noch ${stock} Stück auf Lager!`;
  } else if (stock > 5) {
    urgencySignal =
      market.language === "pl" ? "Dostępny od ręki" : "Sofort lieferbar";
  }

  // SEO
  const seoTitle = `${market.seoPrefix} ${name} | ${market.trustSignal}`;
  const seoDescription = market.metaDescription.replace("{product}", name);

  // JSON-LD structured data
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "Product",
    name,
    description: seoDescription,
    offers: {
      "@type": "Offer",
      price: price.toFixed(2),
      priceCurrency: market.currency,
      availability:
        stock > 0
          ? "https://schema.org/InStock"
          : "https://schema.org/OutOfStock",
      seller: {
        "@type": "Organization",
        name: "ADRION 369",
      },
    },
  };

  return {
    market,
    productSlug: slug,
    pricingCopy,
    trustBadge,
    cta,
    urgencySignal,
    seoTitle,
    seoDescription,
    structuredData,
  };
}

// ═══════════════════════════════════════════════════════════════
// HREFLANG GENERATION
// ═══════════════════════════════════════════════════════════════

/**
 * Generate hreflang link tags for multi-market SEO.
 * Returns HTML string for <head>.
 */
export function generateHreflangTags(slug: string, baseUrl: string): string {
  const markets: MarketCode[] = ["PL", "DE", "AT", "CH"];
  const tags = markets.map((code) => {
    const market = MARKETS[code];
    return `<link rel="alternate" hreflang="${market.hreflang}" href="${baseUrl}/${market.language}/products/${slug}" />`;
  });
  tags.push(
    `<link rel="alternate" hreflang="x-default" href="${baseUrl}/pl/products/${slug}" />`,
  );
  return tags.join("\n");
}

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

function formatPrice(price: number, market: MarketContext): string {
  return new Intl.NumberFormat(market.locale, {
    style: "currency",
    currency: market.currency,
  }).format(price);
}

function slugToName(slug: string): string {
  return slug.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
