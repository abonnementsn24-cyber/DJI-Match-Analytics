import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Sidebar } from "@/components/Sidebar";
import { MobileNav } from "@/components/MobileNav";
import { DemoBanner } from "@/components/DemoBanner";
import { api } from "@/lib/api";
import type { SystemStatus } from "@/lib/types";
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
  title: "EMDJI Match Analytics",
  description: "Football Intelligence & Predictive Analytics",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  let status: SystemStatus | null = null;
  try {
    status = await api.systemStatus();
  } catch {
    status = null;
  }

  return (
    <html
      lang="fr"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full w-full overflow-x-hidden bg-bg text-text">
        <Sidebar />
        <div className="flex min-h-screen w-full min-w-0 flex-1 flex-col">
          <DemoBanner status={status} />
          <main className="w-full min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
          <MobileNav />
        </div>
      </body>
    </html>
  );
}
