"use client";

import { useCut } from "./CutContext";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { ChevronRight, Sun, Moon, User, Activity } from "lucide-react";

export default function Topbar() {
  const { currentCut, setCurrentCut, availableCuts } = useCut();
  const [health, setHealth] = useState<"ok" | "error" | "checking">("checking");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const pathname = usePathname();

  useEffect(() => {
    api.get("/health", { baseURL: "" })
      .then(() => setHealth("ok"))
      .catch(() => setHealth("error"));
  }, []);

  return (
    <header className="h-14 border-b border-zinc-800/60 bg-[#09090b]/95 backdrop-blur-md flex items-center justify-between px-4 lg:px-8 sticky top-0 z-30">
      
      {/* Left: Study Context */}
      <div className="flex items-center gap-4 text-sm pl-12 lg:pl-0">
        <div className="hidden md:flex items-center gap-2 pr-4 border-r border-zinc-800">
          <span className="text-zinc-400 font-medium text-xs">Study</span>
          <span className="text-white font-bold text-xs tracking-wider">ATX-900</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-zinc-500 font-medium text-xs">Path</span>
          <ChevronRight size={14} className="text-zinc-600" />
          <span className="text-zinc-200 font-semibold text-xs capitalize">{pathname.split('/')[1] || 'Overview'}</span>
        </div>
      </div>

      {/* Right: Controls & Profile */}
      <div className="flex items-center gap-6">
        
        {/* Cut / Protocol Selectors */}
        <div className="hidden sm:flex items-center gap-3 bg-zinc-900/50 border border-zinc-800/80 rounded-lg p-1">
          <div className="flex items-center gap-2 px-2 border-r border-zinc-800/80">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Cut</label>
            <select
              className="bg-transparent text-white font-mono text-xs font-bold outline-none cursor-pointer pr-4 appearance-none"
              style={{
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2371717a' viewBox='0 0 16 16'%3E%3Cpath d='M4.646 6.646a.5.5 0 0 1 .708 0L8 9.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E")`,
                backgroundRepeat: "no-repeat",
                backgroundPosition: "right center",
              }}
              value={currentCut}
              onChange={(e) => setCurrentCut(Number(e.target.value))}
            >
              {availableCuts.map((cut) => (
                <option key={cut} value={cut} className="bg-zinc-900 text-white">Cut {cut}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2 px-2">
            <label className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Protocol</label>
            <span className="text-white font-mono text-xs font-bold">v1.0</span>
          </div>
        </div>

        {/* Sync Status */}
        <div className="hidden md:flex flex-col items-end">
          <div className="flex items-center gap-1.5">
            <Activity size={12} className={health === "ok" ? "text-green-500" : "text-red-500"} />
            <span className="text-[10px] text-zinc-400 font-medium">Sync Active</span>
          </div>
          <span className="text-[9px] text-zinc-600 font-mono mt-0.5">Just now</span>
        </div>

        {/* Theme & Profile */}
        <div className="flex items-center gap-3 border-l border-zinc-800/80 pl-6">
          <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} className="text-zinc-400 hover:text-white transition-colors">
            {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
          <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-400">
            <User size={16} />
          </div>
        </div>

      </div>
    </header>
  );
}
