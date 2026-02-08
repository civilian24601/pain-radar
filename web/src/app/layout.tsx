import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { BackgroundMesh } from "@/components/ui/background-mesh";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Pain Radar",
  description: "Decision-grade idea validation. Evidence, not vibes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <BackgroundMesh />
        {children}
      </body>
    </html>
  );
}
