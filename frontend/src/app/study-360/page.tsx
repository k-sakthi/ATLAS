"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, Compass } from "lucide-react";

export default function Study360IndexPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      router.push(`/study-360/${searchTerm.trim()}`);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[75vh] px-4">
      <div className="text-center space-y-6 max-w-2xl w-full fade-in">
        <div className="inline-flex items-center justify-center p-4 bg-purple-500/10 rounded-2xl border border-purple-500/20 mb-2 shadow-[0_0_30px_rgba(168,85,247,0.15)]">
          <Compass size={48} className="text-purple-400" />
        </div>
        
        <div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-purple-300 to-blue-400 mb-4">
            Study 360°
          </h1>
          <p className="text-lg text-zinc-400 font-medium max-w-lg mx-auto leading-relaxed">
            Complete subject-level intelligence across the clinical database. Search for a subject to explore their full study timeline.
          </p>
        </div>

        <form onSubmit={handleSearch} className="w-full relative group mt-8">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-2xl blur-xl transition-all group-hover:blur-2xl opacity-70 group-focus-within:opacity-100 group-focus-within:blur-2xl duration-500"></div>
          <div className="relative bg-[#0a0a0c] border border-zinc-700/50 rounded-2xl flex items-center p-2 shadow-2xl focus-within:border-purple-500/50 transition-colors">
            <div className="pl-4 pr-2 text-zinc-500">
              <Search size={24} />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Enter Subject ID (e.g. 042-S01-001)"
              className="flex-1 bg-transparent border-none outline-none text-zinc-100 text-lg py-4 placeholder-zinc-600 font-mono tracking-wide"
              required
            />
            <button
              type="submit"
              className="bg-purple-600 hover:bg-purple-500 text-white font-bold py-4 px-8 rounded-xl transition-colors ml-2 shadow-[0_0_15px_rgba(147,51,234,0.3)] hover:shadow-[0_0_25px_rgba(147,51,234,0.5)]"
            >
              Explore
            </button>
          </div>
        </form>

        <div className="pt-10 flex items-center justify-center gap-6 text-sm font-medium text-zinc-600">
          <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-zinc-700" /> Timeline Reconstruction</span>
          <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-zinc-700" /> Biomarker Trends</span>
          <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-zinc-700" /> Evidence Traceability</span>
        </div>
      </div>
    </div>
  );
}
