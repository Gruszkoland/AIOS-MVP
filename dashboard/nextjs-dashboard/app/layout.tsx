import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "ADRION 369 — AI Agent Dashboard",
    description: "Real-time monitoring dashboard for the ADRION 369 AI agent swarm",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="pl" className="dark">
            <body className={`${inter.className} min-h-screen bg-background antialiased`}>
                {children}
            </body>
        </html>
    );
}
