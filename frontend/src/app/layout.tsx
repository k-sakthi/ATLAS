import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import { CutProvider } from "@/components/CutContext";
import AIChatPanel from "@/components/AIChatPanel";

export const metadata: Metadata = {
  title: "ATLAS - Clinical Trial Intelligence",
  description: "Deterministic clinical intelligence engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#09090b] text-zinc-200 antialiased selection:bg-blue-500/30">
        <CutProvider>
          <div className="flex min-h-screen bg-[#09090b]">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <Topbar />
              <main className="flex-1 p-4 lg:p-8 overflow-x-hidden">
                {children}
              </main>
            </div>
            <AIChatPanel />
          </div>
        </CutProvider>
      </body>
    </html>
  );
}
