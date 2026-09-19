"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { HelpCircle, RefreshCw, MessageSquare } from "lucide-react";
import EvidencePanel from "@/components/EvidencePanel";

export default function QueriesPage() {
  const [queries, setQueries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: any[] } | null>(null);

  const fetchQueries = async () => {
    setLoading(true);
    try {
      const res = await api.get("/stage2/queries");
      setQueries(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueries();
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 fade-in pb-10">
      <div className="border-b border-zinc-800 pb-6 mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2 flex items-center gap-3">
            <HelpCircle className="text-blue-500" size={32} />
            Query Management
          </h1>
          <p className="text-zinc-400 text-sm font-medium">Stage 2 Data Manager open inquiries.</p>
        </div>
        <button 
          onClick={fetchQueries}
          className="flex items-center gap-2 bg-[#111113] border border-zinc-800 hover:bg-zinc-900 text-zinc-300 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded-lg transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <RefreshCw className="animate-spin text-zinc-500" size={24} />
        </div>
      ) : queries.length === 0 ? (
        <div className="bg-[#111113] border border-zinc-800 rounded-xl p-12 text-center flex flex-col items-center">
          <MessageSquare className="text-zinc-500 mb-4" size={32} />
          <h3 className="text-zinc-200 font-bold text-lg mb-2">No Active Queries</h3>
          <p className="text-zinc-500 text-sm max-w-md">The Data Manager node has not generated any open queries for the current cycle.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {queries.map((q, i) => (
            <div key={i} className="bg-[#111113] border border-zinc-800 rounded-xl p-5 shadow-sm hover:border-zinc-700 transition-colors flex flex-col justify-between h-full">
              <div>
                <div className="flex justify-between items-start mb-3">
                  <span className="bg-blue-900/20 text-blue-400 border border-blue-900/30 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">
                    {q.status || "OPEN"}
                  </span>
                  <span className="font-mono text-[10px] text-zinc-500">{q.query_id || `QRY-${i + 1}`}</span>
                </div>
                <h3 className="text-sm font-bold text-zinc-200 mb-2 leading-snug">{q.text}</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="text-[10px] font-bold uppercase text-zinc-400 bg-[#09090b] px-2 py-1 rounded border border-zinc-800">
                    Site {q.siteid || q.site_id || "UNKNOWN"}
                  </span>
                  <span className="text-[10px] font-bold uppercase text-zinc-400 bg-[#09090b] px-2 py-1 rounded border border-zinc-800">
                    Subject {q.usubjid || q.subject_id || "UNKNOWN"}
                  </span>
                  <span className="text-[10px] font-bold uppercase text-zinc-400 bg-[#09090b] px-2 py-1 rounded border border-zinc-800">
                    {q.domain || q.id?.split("_")[0] || "SOURCE"}
                  </span>
                </div>
              </div>
              <button 
                onClick={() => setSelectedEvidence({
                  title: `Source Record - ${q.usubjid || q.subject_id || q.id || "Query"}`,
                  records: q.evidence?.length ? q.evidence : []
                })}
                className="w-full text-center bg-zinc-900 border border-zinc-700 hover:border-zinc-500 text-zinc-300 py-2 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-colors"
              >
                View Source Record
              </button>
            </div>
          ))}
        </div>
      )}

      <EvidencePanel 
        isOpen={!!selectedEvidence} 
        onClose={() => setSelectedEvidence(null)} 
        title={selectedEvidence?.title || ""} 
        evidence={selectedEvidence?.records || []} 
        emptyMessage="Source record unavailable in the deterministic dataset."
      />
    </div>
  );
}
