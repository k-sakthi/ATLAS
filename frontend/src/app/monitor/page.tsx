"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  ShieldAlert, CheckCircle, XCircle, HelpCircle, Activity, Play, 
  Lock, Brain, Database, FileText, ChevronRight, AlertTriangle, Fingerprint, 
  Server, Cpu, History
} from "lucide-react";

export default function MonitorCommandCenter() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  // Human Gate State
  const [escalations, setEscalations] = useState<any[]>([]);
  const [clarifyText, setClarifyText] = useState("");
  const [activeEscalation, setActiveEscalation] = useState<string | null>(null);

  // Run Config
  const [cut, setCut] = useState(1);
  const [protocol, setProtocol] = useState(1);

  const nodes = [
    { id: "detect", label: "DETECT", icon: Activity, desc: "Identify anomalies" },
    { id: "medical_review", label: "MEDICAL REVIEW", icon: Brain, desc: "Classify findings" },
    { id: "data_manager", label: "DATA MANAGER", icon: Database, desc: "Issue queries" },
    { id: "compliance", label: "COMPLIANCE", icon: FileText, desc: "Verify protocol" },
    { id: "human_gate", label: "HUMAN GATE", icon: ShieldAlert, desc: "Adjudication" },
    { id: "execute", label: "EXECUTE", icon: Play, desc: "Finalize cycle" }
  ];

  const fetchEscalations = async () => {
    try {
      const res = await api.get("/stage2/escalations");
      setEscalations(res.data.filter((e: any) => e.status === "PENDING"));
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchEscalations();
  }, []);

  const runCycle = async () => {
    setLoading(true);
    try {
      const res = await api.post("/stage2/run", { cut, protocol_version: protocol });
      setReport(res.data);
      fetchEscalations();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (id: string, decision: string, reason: string = "") => {
    try {
      await api.post(`/stage2/escalations/${id}/decision`, { decision, reason });
      setClarifyText("");
      setActiveEscalation(null);
      fetchEscalations();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8 fade-in max-w-7xl mx-auto pb-16">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-[#111113] p-6 rounded-2xl border border-zinc-800 shadow-xl">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-3">
            <Server className="text-blue-500" size={28} />
            ReviewCrew Command Center
          </h1>
          <p className="text-zinc-400 text-sm mt-1 font-medium">Stage 2 Autonomous Clinical Monitor Architecture</p>
        </div>
        
        <div className="flex items-center gap-4 bg-[#09090b] p-2 rounded-xl border border-zinc-800">
          <div className="flex items-center gap-2 px-3 border-r border-zinc-800">
            <span className="text-xs text-zinc-500 font-bold uppercase">Cut</span>
            <select value={cut} onChange={(e) => setCut(Number(e.target.value))} className="bg-transparent text-white font-mono text-sm outline-none">
              <option value={1}>1</option>
              <option value={2}>2</option>
            </select>
          </div>
          <div className="flex items-center gap-2 px-3">
            <span className="text-xs text-zinc-500 font-bold uppercase">Protocol</span>
            <select value={protocol} onChange={(e) => setProtocol(Number(e.target.value))} className="bg-transparent text-white font-mono text-sm outline-none">
              <option value={1}>v1</option>
              <option value={2}>v2</option>
            </select>
          </div>
          <button 
            onClick={runCycle} 
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-bold text-sm shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50"
          >
            {loading ? <Activity className="animate-spin" size={16} /> : <Play size={16} fill="currentColor" />}
            {loading ? "Executing..." : "Execute Pipeline"}
          </button>
        </div>
      </div>

      {/* 6-Node Pipeline Visual */}
      <div className="bg-[#111113] p-8 rounded-2xl border border-zinc-800 shadow-xl overflow-x-auto overflow-y-visible custom-scrollbar">
        <h2 className="text-sm font-black text-zinc-500 uppercase tracking-widest mb-6">Execution Architecture</h2>
        <div className="flex items-start justify-between min-w-[900px] min-h-[132px] pb-2">
          {nodes.map((node, i) => {
            const isActive = report !== null;
            const traceEntry = report?.trace?.entries?.find((t: any) => t.node === node.id);
            return (
                <div key={node.id} className="flex items-start flex-1 last:flex-none">
                <div className={`relative flex flex-col items-center w-32 min-h-[124px] ${isActive ? 'opacity-100' : 'opacity-40 grayscale'} transition-all duration-500`}>
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shadow-2xl mb-3 border-2 z-10 ${isActive ? 'bg-zinc-900 border-blue-500/50 text-blue-400' : 'bg-zinc-900 border-zinc-800 text-zinc-500'}`}>
                    <node.icon size={24} />
                  </div>
                  <span className="text-[11px] font-black tracking-wider text-white text-center leading-tight">{node.label}</span>
                  <span className="text-[9px] text-zinc-500 mt-1 uppercase text-center">{node.desc}</span>
                  {traceEntry && (
                    <div className="mt-4 w-48 text-center slide-in-bottom">
                      <span className="inline-block bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] px-2 py-1 rounded truncate max-w-full" title={traceEntry.decision}>
                        {traceEntry.decision}
                      </span>
                    </div>
                  )}
                </div>
                {i < nodes.length - 1 && (
                  <div className="flex-1 h-0.5 mx-2 mt-7 bg-zinc-800 relative">
                    <div className={`absolute top-0 left-0 h-full bg-blue-500 transition-all duration-1000 ${isActive ? 'w-full shadow-[0_0_8px_#3b82f6]' : 'w-0'}`} />
                    <ChevronRight size={16} className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 ${isActive ? 'text-blue-500' : 'text-zinc-700'}`} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Risk Intelligence */}
        <div className="bg-[#111113] border border-zinc-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-sm font-black text-white uppercase flex items-center gap-2 mb-6">
            <AlertTriangle className="text-amber-500" size={18} />
            Risk Intelligence
          </h2>
          {!report ? (
            <p className="text-sm text-zinc-500">Run a cycle to calculate risks.</p>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-red-950/20 border border-red-900/30 rounded-xl">
                <span className="text-sm font-bold text-red-400">CRITICAL Risk (SAE/Hy&apos;s Law)</span>
                <span className="badge badge-red text-lg px-3 py-1">
                  {report.memory_state?.escalations?.filter((e: any) => e.severity === 'CRITICAL').length || 0}
                </span>
              </div>
              <div className="flex items-center justify-between p-4 bg-amber-950/20 border border-amber-900/30 rounded-xl">
                <span className="text-sm font-bold text-amber-400">HIGH Risk (Site/Recurring)</span>
                <span className="badge badge-amber text-lg px-3 py-1">
                  {report.memory_state?.escalations?.filter((e: any) => e.severity === 'HIGH').length || 0}
                </span>
              </div>
              <div className="text-xs text-zinc-500 mt-2 flex items-center gap-2">
                <CheckCircle size={12} className="text-green-500" /> Values dynamically extracted from deterministic `Escalation` severity flags.
              </div>
            </div>
          )}
        </div>

        {/* Security */}
        <div className="bg-[#111113] border border-zinc-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
          <h2 className="text-sm font-black text-white uppercase flex items-center gap-2 mb-6 relative z-10">
            <Lock className="text-purple-500" size={18} />
            Security & Audit
          </h2>
          <div className="space-y-3 relative z-10">
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
              <span className="text-xs font-bold text-zinc-400">Input/Evidence Validation</span>
              <span className="badge badge-gray">Not Implemented</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
              <span className="text-xs font-bold text-zinc-400">Access Control / IAM</span>
              <span className="badge badge-gray">Not Implemented</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
              <span className="text-xs font-bold text-zinc-400">Prompt-Injection Protection</span>
              <span className="badge badge-gray">Not Implemented</span>
            </div>
          </div>
          <div className="mt-4 p-3 bg-red-950/20 border border-red-900/30 rounded-lg text-xs text-red-400 font-medium">
            <AlertTriangle size={14} className="inline mr-1" />
            Backend capability missing. Stage 1/2 deterministic engine does not currently output security trace schemas.
          </div>
        </div>

        {/* Memory */}
        <div className="bg-[#111113] border border-zinc-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-sm font-black text-white uppercase flex items-center gap-2 mb-6">
            <Cpu className="text-green-500" size={18} />
            Memory Architecture
          </h2>
          {!report ? (
            <p className="text-sm text-zinc-500">Run a cycle to view memory state.</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-800">
                  <div className="text-2xl font-black text-white">{report.memory_state?.queries?.length || 0}</div>
                  <div className="text-xs text-zinc-500 font-bold uppercase mt-1">Total Queries</div>
                  <div className="text-[10px] text-green-400 mt-2">Duplicate Prevention: ACTIVE</div>
                </div>
                <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-800">
                  <div className="text-2xl font-black text-white">{report.memory_state?.escalations?.length || 0}</div>
                  <div className="text-xs text-zinc-500 font-bold uppercase mt-1">Total Escalations</div>
                  <div className="text-[10px] text-green-400 mt-2">Duplicate Prevention: ACTIVE</div>
                </div>
              </div>
              <div className="p-4 bg-zinc-900 rounded-xl border border-zinc-800">
                <span className="text-xs font-bold text-zinc-400 block mb-2">Recurring Problems Detected</span>
                <div className="flex gap-2">
                  <span className="badge badge-blue">{report.site_flags} Site Flags</span>
                  <span className="badge badge-purple">{report.memory_state?.escalations?.filter((e:any)=>e.code.includes('RECURRING')).length || 0} Subject Flags</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Trace Log */}
        <div className="bg-[#111113] border border-zinc-800 rounded-2xl p-6 shadow-xl">
          <h2 className="text-sm font-black text-white uppercase flex items-center gap-2 mb-6">
            <Fingerprint className="text-indigo-500" size={18} />
            Execution Trace
          </h2>
          {!report ? (
            <p className="text-sm text-zinc-500">Run a cycle to generate trace log.</p>
          ) : (
            <div className="space-y-3 max-h-[250px] overflow-y-auto custom-scrollbar pr-2">
              {report.trace?.entries?.map((t: any, idx: number) => (
                <div key={idx} className="bg-zinc-900 p-3 rounded-lg border border-zinc-800 flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-black text-indigo-400 uppercase tracking-wider">{t.node}</span>
                  </div>
                  <p className="text-xs text-zinc-300 font-mono">{t.decision}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Human Gate Section */}
      <div className="bg-[#111113] border border-zinc-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-sm font-black text-white uppercase flex items-center gap-2">
            <ShieldAlert className="text-amber-500" size={18} />
            Human Gate (Pending Decisions)
          </h2>
          <span className="badge badge-amber">{escalations.length} Pending</span>
        </div>

        {escalations.length === 0 ? (
          <div className="text-zinc-500 text-sm p-8 bg-[#09090b] border border-zinc-800/50 rounded-xl text-center font-medium">
            <CheckCircle size={32} className="mx-auto text-green-700/50 mb-3" />
            No pending escalations require adjudication.
          </div>
        ) : (
          <div className="space-y-6">
            {escalations.map((esc) => (
              <div key={esc.id} className="bg-[#09090b] border border-amber-900/30 rounded-xl overflow-hidden">
                <div className="bg-amber-950/10 border-b border-amber-900/20 p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="badge badge-amber">{esc.severity}</span>
                    <span className="text-zinc-200 font-mono font-bold">{esc.usubjid}</span>
                  </div>
                  <span className="text-[10px] text-zinc-500 uppercase">Cycle {esc.cycle}</span>
                </div>
                
                <div className="p-5 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-bold text-amber-400 mb-3">{esc.summary}</h3>
                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Deterministic Evidence</h4>
                    <div className="bg-[#111113] border border-zinc-800 rounded-lg p-3 font-mono text-[10px] text-zinc-400 max-h-32 overflow-y-auto custom-scrollbar whitespace-pre-wrap">
                      {JSON.stringify(esc.evidence, null, 2)}
                    </div>
                  </div>
                  
                  <div className="flex flex-col justify-between">
                    <div>
                      <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Actions</h4>
                      <div className="flex flex-wrap gap-2">
                        <button onClick={() => handleDecision(esc.id, "APPROVED", "Approved")} className="flex-1 flex items-center justify-center gap-1.5 bg-green-950/40 hover:bg-green-900/60 text-green-400 border border-green-900/40 px-3 py-2 rounded-lg font-bold text-xs transition-colors">
                          <CheckCircle size={14} /> Approve
                        </button>
                        <button onClick={() => handleDecision(esc.id, "REJECTED", "Downgraded")} className="flex-1 flex items-center justify-center gap-1.5 bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-900/40 px-3 py-2 rounded-lg font-bold text-xs transition-colors">
                          <XCircle size={14} /> Reject
                        </button>
                        <button onClick={() => setActiveEscalation(activeEscalation === esc.id ? null : esc.id)} className="flex-1 flex items-center justify-center gap-1.5 bg-blue-950/40 hover:bg-blue-900/60 text-blue-400 border border-blue-900/40 px-3 py-2 rounded-lg font-bold text-xs transition-colors">
                          <HelpCircle size={14} /> Clarify
                        </button>
                      </div>

                      {activeEscalation === esc.id && (
                        <div className="bg-[#111113] border border-blue-900/30 p-3 rounded-lg mt-3 slide-in-bottom">
                          <textarea
                            value={clarifyText}
                            onChange={(e) => setClarifyText(e.target.value)}
                            className="w-full bg-black/50 border border-zinc-800 text-zinc-200 text-xs rounded p-2 outline-none focus:border-blue-500 transition-colors resize-none mb-2"
                            rows={2}
                            placeholder="Request evidence (e.g., 'What were the screening labs?')"
                          />
                          <button onClick={() => handleDecision(esc.id, "CLARIFY", clarifyText)} disabled={!clarifyText.trim()} className="w-full py-1.5 text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50">Submit Request</button>
                        </div>
                      )}
                    </div>

                    {esc.clarification_history?.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-zinc-800/50">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Clarification History</h4>
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {esc.clarification_history.map((ch: any, idx: number) => (
                            <div key={idx} className="bg-zinc-900/50 p-2 rounded border border-zinc-800/50 text-[11px]">
                              <p className="text-zinc-400 mb-1"><strong className="text-blue-400">Q:</strong> {ch.question}</p>
                              <p className="text-zinc-300"><strong className="text-green-400">A:</strong> {ch.answer}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
