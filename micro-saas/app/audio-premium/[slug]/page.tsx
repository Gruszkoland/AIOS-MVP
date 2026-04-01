import { notFound } from "next/navigation";
import Image from "next/image";
import fs from "fs/promises";
import path from "path";
import { ProductCheckout } from "@/components/product-checkout";

// T=0.8 - BoosterLever Optimization for High Conversion
// ADRION 369 v2.0 - Sniper Single Product Page (SPP) + Mass Generator v2.6

interface ManifestProduct {
  slug: string;
  sku: string;
  name: string;
  channel: string;
  wholesalePrice: number;
  retailPriceDE: number | null;
  retailPricePL: number | null;
  marginPct: number;
  stock: number;
  supplier: string;
  vortexResonance: number | null;
  vortexPass: boolean;
  solfeggioHz: number;
  status: string;
  scoutedAt: string | null;
  markets: Record<
    string,
    { seoTitle: string; seoDescription: string; slug: string }
  >;
}

interface Manifest {
  generated_at: string;
  total_products: number;
  channels: Record<string, number>;
  products: ManifestProduct[];
  staticParams: Array<{ slug: string }>;
}

const MANIFEST_PATH = path.join(process.cwd(), "data", "product-manifest.json");

async function loadManifest(): Promise<Manifest | null> {
  try {
    const raw = await fs.readFile(MANIFEST_PATH, "utf-8");
    return JSON.parse(raw) as Manifest;
  } catch {
    return null;
  }
}

export async function generateStaticParams() {
  const manifest = await loadManifest();
  if (!manifest) return [];
  return manifest.staticParams;
}

export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}) {
  const manifest = await loadManifest();
  const product = manifest?.products.find((p) => p.slug === params.slug);
  if (!product) return {};
  const deMeta = product.markets["DE"];
  return {
    title: deMeta?.seoTitle ?? product.name,
    description: deMeta?.seoDescription ?? `${product.name} wholesale`,
  };
}

async function getWholesaleProduct(
  slug: string,
): Promise<ManifestProduct | null> {
  const manifest = await loadManifest();
  if (!manifest) return null;
  return manifest.products.find((p) => p.slug === slug) ?? null;
}

const CHANNEL_LABELS: Record<string, string> = {
  AUDIO_PREMIUM: "Premium Audio",
  SMART_ENERGY: "Smart Energy",
  ROBOTICS_AI: "Robotics & AI",
  REFURBISHED_LUX: "Refurbished Luxury",
  BIOTECH_HEALTH: "Biotech & Health",
};

export default async function WholesalePage({
  params,
}: {
  params: { slug: string };
}) {
  const product = await getWholesaleProduct(params.slug);

  if (!product) {
    notFound();
  }

  const category = CHANNEL_LABELS[product.channel] ?? product.channel;
  const retailPrice =
    product.retailPricePL ?? product.retailPriceDE ?? product.wholesalePrice;
  const referencePrice = retailPrice * 1.2; // Estimated retail before wholesale

  return (
    <div className="min-h-screen bg-white text-black p-8 font-sans">
      <div className="max-w-4xl mx-auto flex flex-col md:flex-row gap-8">
        {/* Product Image Placeholder */}
        <div className="w-full md:w-1/2 aspect-square bg-gray-100 flex items-center justify-center rounded-lg border">
          <span className="text-gray-400">[Wizualizacja Vortex-Phi]</span>
        </div>

        {/* Sales Copy - BoosterLever Mode */}
        <div className="w-full md:w-1/2 space-y-6">
          <nav className="text-sm text-gray-500">
            {category} &gt; {product.sku}
          </nav>

          <h1 className="text-3xl font-bold tracking-tight">{product.name}</h1>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-red-600">
              {retailPrice.toFixed(2)} PLN
            </span>
            <span className="text-sm text-gray-500 line-through">
              {referencePrice.toFixed(2)} PLN
            </span>
            <span className="ml-2 text-sm font-semibold text-green-700 bg-green-100 px-2 py-0.5 rounded">
              −{product.marginPct.toFixed(1)}%
            </span>
          </div>

          <div className="p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-green-800 text-sm font-semibold flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              DOSTĘPNE U DYSTRYBUTORA: {product.stock} szt.
            </p>
            <p className="text-green-700 text-xs mt-1">
              Wysyłka bezpośrednia z magazynu centralnego ({product.solfeggioHz}
              Hz Logistics).
            </p>
          </div>

          {product.vortexPass && (
            <div className="flex items-center gap-2 text-xs text-purple-700 bg-purple-50 px-3 py-2 rounded">
              <span className="w-2 h-2 bg-purple-500 rounded-full" />
              Vortex Resonance: {product.vortexResonance} |{" "}
              {product.solfeggioHz}Hz
            </div>
          )}

          <p className="text-gray-700 leading-relaxed text-sm">
            Wholesale from <strong>{product.supplier}</strong> | Channel:{" "}
            {category}
          </p>

          <ProductCheckout
            sku={product.sku}
            name={product.name}
            price={retailPrice}
          />

          <div className="grid grid-cols-2 gap-4 pt-4 border-t text-center">
            <div className="text-xs text-gray-400">
              Gwarancja Oryginalności
              <br />
              (Law 6: Authenticity)
            </div>
            <div className="text-xs text-gray-400">
              Bezpośrednia Dostawa
              <br />
              (G2: Harmony)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
