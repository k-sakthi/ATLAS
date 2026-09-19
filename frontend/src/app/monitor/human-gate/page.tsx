"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ShieldCheck, AlertCircle, RefreshCw, MessageSquare, Check, X, FileText, ChevronDown, Workflow } from "lucide-react";
import EvidencePanel from "@/components/EvidencePanel";

export default function HumanGatePage() {
  const [escalations, setEscalations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState<string | null>(null);
  const [clarifyText, setClarifyText] = useState<string>("");
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: any[] } | null>(null);

  const fetchEscalations = async () => {
    setLoading(true);
    try {
      const res = await api.get("/stage2/escalations");
      setEscalations(res.data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalations();
  }, []);

  const handleAction = async (id: string, decision: "APPROVED" | "REJECTED" | "CLARIFY") => {
    if (decision === "CLARIFY" && !clarifyText.trim()) return;
    setActioningId(id);
    try {
      await api.post(`/stage2/escalations/${id}/decision`, {
        decision,
        reason: decision === "CLARIFY" ? clarifyText : `Manually ${decision.toLowerCase()} by monitor`,
      });
      if (decision === "CLARIFY") {
        setClarifyText("");
        await fetchEscalations(); // Refresh to see the backend response
      } else {
        setEscalations((prev) => prev.filter((e) => e.id !== id));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActioningId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 fade-in pb-10">
      
      {/* Header */}
      <div className="border-b border-zinc-800 pb-6 mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white mb-2 flex items-center gap-3">
            <ShieldCheck className="text-amber-500" size={32} />
            Human Gate
          </h1>
          <p className="text-zinc-400 text-sm font-medium">Dedicated decision workspace for ReviewCrew escalations.</p>
        </div>
        <button 
          onClick={fetchEscalations}
          className="flex items-center gap-2 bg-[#111113] border border-zinc-800 hover:bg-zinc-900 text-zinc-300 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded-lg transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <RefreshCw className="animate-spin text-zinc-500" size={24} />
        </div>
      ) : escalations.length === 0 ? (
        <div className="bg-[#111113] border border-zinc-800 rounded-xl p-12 text-center flex flex-col items-center">
          <div className="w-16 h-16 bg-zinc-900/50 rounded-full flex items-center justify-center mb-4">
            <Check className="text-zinc-500" size={32} />
          </div>
          <h3 className="text-zinc-200 font-bold text-lg mb-2">No Pending Escalations</h3>
          <p className="text-zinc-500 text-sm max-w-md">All ReviewCrew escalations have been adjudicated. The Human Gate queue is currently clear.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {escalations.map((esc) => (
            <div key={esc.id} className="bg-[#111113] border border-zinc-800 rounded-xl shadow-sm overflow-hidden">
              {/* Header */}
              <div className="bg-[#09090b] border-b border-zinc-800 p-5 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-xs font-bold text-zinc-500">{esc.id}</span>
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      esc.severity === 'CRITICAL' ? 'bg-red-950/50 text-red-400 border border-red-900/50' : 
                      esc.severity === 'HIGH' ? 'bg-amber-950/50 text-amber-400 border border-amber-900/50' : 
                      'bg-blue-950/50 text-blue-400 border border-blue-900/50'
                    }`}>
                      {esc.severity}
                    </span>
                    <span className="px-2.5 py-0.5 rounded bg-zinc-800/50 text-zinc-300 text-[10px] font-bold uppercase tracking-wider border border-zinc-700/50">
                      Site {esc.siteid || "UNKNOWN"}
                    </span>
                    <span className="px-2.5 py-0.5 rounded bg-zinc-800/50 text-zinc-300 text-[10px] font-bold uppercase tracking-wider border border-zinc-700/50">
                      Subject {esc.usubjid || "UNKNOWN"}
                    </span>
                  </div>
                  <h3 className="text-zinc-200 font-bold text-lg">{esc.summary}</h3>
                </div>
                <button 
                  onClick={() => setSelectedEvidence({ title: `Evidence for ${esc.id}`, records: esc.evidence || [] })}
                  className="flex items-center gap-2 bg-zinc-900 border border-zinc-700 hover:border-zinc-500 text-zinc-300 px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-colors"
                >
                  <FileText size={14} /> View Evidence
                </button>
              </div>

              {/* Body */}
              <div className="p-5 space-y-6">
                {esc.clarification_history && esc.clarification_history.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider">Clarification History</h4>
                    <div className="bg-[#09090b] border border-zinc-800 rounded-lg p-4 space-y-4">
                      {esc.clarification_history.map((h: any, i: number) => (
                        <div key={i} className="space-y-2">
                          <div className="flex gap-3">
                            <div className="w-6 h-6 rounded-full bg-blue-900/30 flex items-center justify-center flex-shrink-0 mt-0.5"><ShieldCheck size={12} className="text-blue-400" /></div>
                            <div>
                              <div className="text-[11px] font-bold text-blue-400 uppercase tracking-wider mb-1">Human Monitor</div>
                              <div className="text-sm text-zinc-300">{h.question}</div>
                            </div>
                          </div>
                          <div className="flex gap-3">
                            <div className="w-6 h-6 rounded-full bg-amber-900/30 flex items-center justify-center flex-shrink-0 mt-0.5"><Workflow size={12} className="text-amber-400" /></div>
                            <div>
                              <div className="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1">ReviewCrew Graph</div>
                              <div className="text-sm text-zinc-400 font-mono bg-zinc-900/50 p-3 rounded border border-zinc-800">{h.answer}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Protocol Context</h4>
                    <p className="text-sm text-zinc-300 leading-relaxed bg-[#09090b] p-3 rounded-lg border border-zinc-800/80">{esc.protocol_context}</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Alternatives Considered</h4>
                    <ul className="text-sm text-zinc-300 space-y-2 bg-[#09090b] p-3 rounded-lg border border-zinc-800/80">
                      {esc.alternatives_considered?.map((alt: string, i: number) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-zinc-600 mt-1">•</span>
                          <span>{alt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Actions */}
                <div className="border-t border-zinc-800/80 pt-5 mt-5">
                  <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <div className="flex-1 w-full max-w-xl flex gap-2">
                      <input 
                        type="text" 
                        value={clarifyText}
                        onChange={(e) => setClarifyText(e.target.value)}
                        placeholder="Ask ReviewCrew to check deterministic graph..."
                        className="flex-1 bg-[#09090b] border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200 focus:outline-none focus:border-blue-500"
                      />
                      <button 
                        onClick={() => handleAction(esc.id, "CLARIFY")}
                        disabled={!clarifyText.trim() || actioningId === esc.id}
                        className="bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors flex items-center gap-2"
                      >
                        <MessageSquare size={16} /> Clarify
                      </button>
                    </div>
                    <div className="flex items-center gap-3 w-full md:w-auto">
                      <button 
                        onClick={() => handleAction(esc.id, "REJECTED")}
                        disabled={actioningId === esc.id}
                        className="flex-1 md:flex-none bg-red-950/30 hover:bg-red-900/50 border border-red-900/50 text-red-400 px-6 py-2 rounded-lg text-sm font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2"
                      >
                        <X size={16} /> Reject
                      </button>
                      <button 
                        onClick={() => handleAction(esc.id, "APPROVED")}
                        disabled={actioningId === esc.id}
                        className="flex-1 md:flex-none bg-green-950/30 hover:bg-green-900/50 border border-green-900/50 text-green-400 px-6 py-2 rounded-lg text-sm font-bold uppercase tracking-wider transition-colors flex items-center justify-center gap-2"
                      >
                        <Check size={16} /> Approve
                      </button>
                    </div>
                  </div>
                  <p className="text-[10px] text-zinc-600 mt-3 flex items-center gap-1.5">
                    <AlertCircle size={12} />
                    CLARIFY retrieves information purely from the deterministic graph/backend.
                  </p>
                </div>
              </div>
            </div>
          ))}
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
