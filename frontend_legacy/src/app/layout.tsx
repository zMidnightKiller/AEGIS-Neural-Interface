import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HELEN AI | Intelligent Assistant",
  description: "Adaptive Engineered General Intelligence System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} relative min-h-screen overflow-hidden`}>
        <div className="scanline" />
        <div className="fixed inset-0 bg-[radial-gradient(circle_at_center,_var(--surface)_0%,_var(--background)_100%)] opacity-50 pointer-events-none" />
        {children}
      </body>
    </html>
  );
}
