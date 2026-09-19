"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { PlayCircle, CheckCircle, Database, FileText, Fingerprint, ChevronRight } from "lucide-react";
import EvidencePanel from "@/components/EvidencePanel";

export default function CycleReportPage() {
  const [cut, setCut] = useState(5);
  const [protocolVersion, setProtocolVersion] = useState(2);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: any[] } | null>(null);

  const handleRunCycle = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/stage2/run", { cut, protocol_version: protocolVersion });
      setReport(res.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to run cycle.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 fade-in max-w-6xl mx-auto pb-10">
      
      {/* Header */}
      <div className="border-b border-zinc-800 pb-6 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2 flex items-center gap-3">
            <FileText className="text-purple-500" size={32} />
            Cycle Reports
          </h1>
          <p className="text-zinc-400 text-sm font-medium">Execute and inspect Stage 2 batch runs.</p>
        </div>
      </div>

      {/* Execution Controls */}
      <div className="bg-[#111113] border border-zinc-800 rounded-xl p-6 shadow-sm flex flex-wrap gap-6 items-end">
        <div>
          <label className="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-2">Data Cut</label>
          <input type="number" value={cut} onChange={(e) => setCut(Number(e.target.value))} className="bg-[#09090b] border border-zinc-800 text-zinc-200 text-sm font-semibold rounded-lg p-2.5 w-24 outline-none focus:border-purple-500" />
        </div>
        <div>
          <label className="block text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-2">Protocol Version</label>
          <input type="number" value={protocolVersion} onChange={(e) => setProtocolVersion(Number(e.target.value))} className="bg-[#09090b] border border-zinc-800 text-zinc-200 text-sm font-semibold rounded-lg p-2.5 w-24 outline-none focus:border-purple-500" />
        </div>
        <button 
          onClick={handleRunCycle} 
          disabled={loading} 
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white px-6 py-2.5 rounded-lg font-bold text-sm transition-colors shadow-sm disabled:opacity-50 ml-auto md:ml-0"
        >
          {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><PlayCircle size={18} /> Execute Pipeline</>}
        </button>
      </div>

      {error && (
        <div className="bg-red-950/20 border border-red-900/40 text-red-400 p-4 rounded-lg text-sm font-semibold flex items-center gap-2">
          {error}
        </div>
      )}

      {/* Cycle Report */}
      {report && (
        <div className="space-y-6 fade-in">
          
          <div className="bg-[#111113] border border-zinc-800 rounded-xl overflow-hidden shadow-sm">
            {/* Report Header */}
            <div className="bg-[#09090b] border-b border-zinc-800 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <CheckCircle className="text-green-500" size={20}/> 
                  Cycle {report.cycle} Successful
                </h2>
                <div className="flex gap-4 mt-2 text-xs text-zinc-400 font-medium">
                  <span>Data Cut: <strong className="text-white">{report.cut}</strong></span>
                  <span>Protocol: <strong className="text-white">v{report.protocol_version || protocolVersion}</strong></span>
                  <span>Timestamp: <strong className="text-white font-mono">{new Date().toLocaleTimeString()}</strong></span>
                </div>
              </div>
            </div>
            
            {/* Key Findings */}
            <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4 bg-[#111113]">
              <div className="bg-[#09090b] p-4 rounded-lg border border-zinc-800/80">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider block mb-1">Total Findings</span>
                <div className="text-3xl font-black text-white">{report.findings}</div>
              </div>
              <div className="bg-amber-950/10 p-4 rounded-lg border border-amber-900/30">
                <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider block mb-1">Escalations</span>
                <div className="text-3xl font-black text-amber-400">{report.escalations}</div>
              </div>
              <div className="bg-blue-950/10 p-4 rounded-lg border border-blue-900/30">
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-wider block mb-1">Queries Raised</span>
                <div className="text-3xl font-black text-blue-400">{report.queries}</div>
              </div>
              <div className="bg-purple-950/10 p-4 rounded-lg border border-purple-900/30">
                <span className="text-[10px] font-bold text-purple-500 uppercase tracking-wider block mb-1">Deviations</span>
                <div className="text-3xl font-black text-purple-400">{report.deviations}</div>
              </div>
            </div>
          </div>

          {/* Trace Preview */}
          <div className="bg-[#111113] border border-zinc-800 rounded-xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center gap-2">
                <Fingerprint className="text-zinc-500" size={18} />
                Execution Trace
              </h3>
            </div>
            
            <div className="flex items-center justify-between overflow-x-auto pb-4 custom-scrollbar">
              {['detect', 'medical_review', 'data_manager', 'compliance', 'human_gate', 'execute'].map((node, i, arr) => {
                const entry = report.trace?.entries?.find((e: any) => e.node === node);
                const isActive = !!entry;
                
                return (
                  <div key={node} className="flex items-center flex-shrink-0">
                    <div className={`flex flex-col items-center justify-center w-24 h-24 rounded-full border-2 ${isActive ? 'bg-purple-950/20 border-purple-900/50 text-purple-400' : 'bg-[#09090b] border-zinc-800 text-zinc-600'} shadow-sm`}>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-center px-2">{node.replace('_', ' ')}</span>
                    </div>
                    {i < arr.length - 1 && (
                      <div className={`w-8 h-0.5 mx-2 ${isActive ? 'bg-purple-900/50' : 'bg-zinc-800'}`} />
                    )}
                  </div>
                );
              })}
            </div>

            <div className="mt-6 space-y-3">
              {report.trace?.entries?.map((entry: any, i: number) => (
                <div key={i} className="flex flex-col md:flex-row gap-4 bg-[#09090b] p-4 rounded-lg border border-zinc-800/80">
                  <div className="w-32 flex-shrink-0">
                    <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider bg-purple-950/30 px-2 py-1 rounded border border-purple-900/30">{entry.node.replace('_', ' ')}</span>
                  </div>
                  <div className="flex-1 text-sm text-zinc-300 font-medium">{entry.decision}</div>
                  <button 
                    onClick={() => setSelectedEvidence({ title: `Trace: ${entry.node}`, records: entry.evidence || [] })}
                    className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 hover:text-white transition-colors h-max"
                  >
                    View Context
                  </button>
                </div>
              ))}
            </div>

          </div>
        </div>
      )}

      <EvidencePanel 
        isOpen={!!selectedEvidence} 
        onClose={() => setSelectedEvidence(null)} 
        title={selectedEvidence?.title || ""} 
        evidence={selectedEvidence?.records || []} 
      />
    </div>
  );
}
