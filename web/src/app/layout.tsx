import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { SWRProvider } from "@/components/swr-provider";
import "./globals.css";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "SEHRA Analysis Platform",
  description: "School Eye Health Rapid Assessment Analysis Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <SWRProvider>
          {children}
        </SWRProvider>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
