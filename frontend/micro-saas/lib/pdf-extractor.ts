export type PdfExtractionResult = {
  text: string;
  numPages: number;
  parseMode: "real" | "mock";
};

function normalizeWhitespace(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}

export async function extractPdfText(fileBuffer: ArrayBuffer): Promise<PdfExtractionResult> {
  try {
    const pdfParseModule = await import("pdf-parse");
    const pdfParse = (pdfParseModule.default ?? pdfParseModule) as (buffer: Buffer) => Promise<{ text: string; numpages: number }>;

    const parsed = await pdfParse(Buffer.from(fileBuffer));
    const normalizedText = normalizeWhitespace(parsed.text || "");

    return {
      text: normalizedText,
      numPages: parsed.numpages || 1,
      parseMode: normalizedText.length > 0 ? "real" : "mock",
    };
  } catch {
    return {
      text: "",
      numPages: 1,
      parseMode: "mock",
    };
  }
}
