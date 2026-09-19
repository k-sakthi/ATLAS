"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard, Compass, ShieldAlert, TestTube, AlertTriangle, 
  ClipboardCheck, Pill, Ban, GitCompare, Activity, FileText, 
  HelpCircle, Fingerprint, Menu, X, Database, Workflow, ShieldCheck, Users
} from "lucide-react";
import { api } from "@/lib/api";

const mainItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Subjects", href: "/subjects", icon: Users },
  { name: "Study 360°", href: "/study-360", icon: Compass },
  { name: "Safety", href: "/safety", icon: ShieldAlert },
  { name: "Laboratory", href: "/labs", icon: TestTube },
  { name: "Events", href: "/sae", icon: AlertTriangle }, // Merged SAE/TEAE mentally or just pointing to /sae
  { name: "Compliance", href: "/protocol-deviations", icon: ClipboardCheck },
  { name: "Dosing", href: "/dosing", icon: Pill },
  { name: "Medications", href: "/prohibited-medications", icon: Ban },
  { name: "Compare", href: "/compare", icon: GitCompare },
];

const monitorItems = [
  { name: "Surveillance (Stage 3)", href: "/surveillance", icon: Activity },
  { name: "ReviewCrew", href: "/monitor", icon: Workflow },
  { name: "Human Gate", href: "/monitor/human-gate", icon: ShieldCheck }, 
  { name: "Cycle Reports", href: "/monitor/cycle", icon: FileText },
  { name: "Queries", href: "/monitor/queries", icon: HelpCircle },
  { name: "Trace", href: "/monitor/trace", icon: Fingerprint },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [health, setHealth] = useState<"ok" | "error" | "checking">("checking");

  useEffect(() => {
    api.get("/health", { baseURL: "" })
      .then(() => setHealth("ok"))
      .catch(() => setHealth("error"));
  }, []);

  return (
    <>
      {/* Mobile toggle */}
      {!collapsed && (
        <div
          className="fixed inset-0 bg-black/80 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setCollapsed(true)}
        />
      )}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="fixed top-3 left-4 z-50 lg:hidden bg-[#18181b] border border-zinc-800 p-2 rounded text-zinc-400 hover:text-white shadow-lg"
      >
        {collapsed ? <Menu size={20} /> : <X size={20} />}
      </button>

      <aside
        className={`fixed lg:sticky top-0 left-0 z-40 h-screen w-[260px] bg-[#09090b] border-r border-zinc-800/60 flex flex-col transition-transform duration-300 ${
          collapsed ? "-translate-x-full lg:translate-x-0" : "translate-x-0"
        }`}
      >
        {/* Brand */}
        <div className="px-6 pt-6 pb-6 border-b border-zinc-800/40">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded bg-white flex items-center justify-center text-black font-black text-lg shadow-[0_0_15px_rgba(255,255,255,0.15)]">
              A
            </div>
            <div>
              <h1 className="text-[16px] font-black tracking-tight text-white leading-none">
                ATLAS
              </h1>
              <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mt-1">
                Operations Center
              </p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-6 space-y-8 custom-scrollbar">
          
          {/* Main Items */}
          <ul className="space-y-1">
            {mainItems.map((item) => {
              const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    onClick={() => setCollapsed(true)}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? "bg-zinc-800/50 text-white shadow-sm"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                    }`}
                  >
                    <item.icon size={16} className={isActive ? "text-blue-400" : "text-zinc-500"} />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>

          {/* Monitor */}
          <div>
            <p className="px-3 mb-3 text-[10px] font-bold text-zinc-600 uppercase tracking-widest">
              Monitor (Stage 2)
            </p>
            <ul className="space-y-1">
              {monitorItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <li key={item.name}>
                    <Link
                      href={item.href}
                      onClick={() => setCollapsed(true)}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? "bg-zinc-800/50 text-white shadow-sm"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                      }`}
                    >
                      <item.icon size={16} className={isActive ? "text-amber-400" : "text-zinc-500"} />
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>

        {/* Bottom Status */}
        <div className="p-4 border-t border-zinc-800/60 bg-[#09090b]">
          <div className="bg-[#111113] border border-zinc-800 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Database size={12} className="text-zinc-500" />
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">System Status</span>
            </div>
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="text-zinc-300">Backend</span>
              <div className="flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 rounded-full ${health === 'ok' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={health === 'ok' ? 'text-green-500' : 'text-red-500'}>
                  {health === 'ok' ? 'Connected' : 'Offline'}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs font-medium mt-1">
              <span className="text-zinc-300">Environment</span>
              <span className="text-blue-400">Production</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
