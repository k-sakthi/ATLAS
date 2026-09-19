"use client";

import { Fingerprint, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function TracePage() {
  return (
    <div className="space-y-8 fade-in max-w-6xl mx-auto pb-10">
      
      {/* Header */}
      <div className="border-b border-zinc-800 pb-6">
        <h1 className="text-3xl font-black tracking-tight text-white mb-2 flex items-center gap-3">
          <Fingerprint className="text-zinc-500" size={32} />
          Trace Log
        </h1>
        <p className="text-zinc-400 text-sm font-medium">Audit logs for deterministic system execution.</p>
      </div>

      <div className="bg-[#111113] border border-zinc-800 rounded-xl p-12 text-center flex flex-col items-center">
        <AlertCircle className="text-zinc-500 mb-4" size={48} />
        <h3 className="text-zinc-200 font-bold text-lg mb-2">Live Trace Logging</h3>
        <p className="text-zinc-500 text-sm max-w-lg mb-6 leading-relaxed">
          The Stage 2 deterministic backend generates an immutable execution trace exclusively during the batch run. To view the complete 6-node trace (Detect → Medical Review → Data Manager → Compliance → Human Gate → Execute), please execute a cycle.
        </p>
        <Link 
          href="/monitor/cycle"
          className="bg-purple-900/30 border border-purple-900/50 hover:bg-purple-900/50 text-purple-400 font-bold text-sm px-6 py-2.5 rounded-lg transition-colors uppercase tracking-wider"
        >
          Execute Cycle Report
        </Link>
      </div>

    </div>
  );
}
