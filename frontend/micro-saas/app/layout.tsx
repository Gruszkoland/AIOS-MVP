import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PDF Signal Room",
  description: "Micro-SaaS MVP for extracting decision-ready signals from PDFs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="page-shell grain">{children}</div>
      </body>
    </html>
  );
}
