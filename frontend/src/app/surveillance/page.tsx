"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { 
  Activity, ShieldAlert, ShieldCheck, AlertTriangle, AlertOctagon, 
  Search, CheckCircle2, XCircle, Clock, ChevronRight, FileWarning, Fingerprint, Database, GitMerge, FileText
} from "lucide-react";

export default function SurveillanceDashboard() {
  const [state, setState] = useState<any>(null);
  const [risks, setRisks] = useState<any[]>([]);
  const [adv, setAdv] = useState<any>(null);
  const [escalations, setEscalations] = useState<any[]>([]);
  const [corrections, setCorrections] = useState<any[]>([]);
  const [trace, setTrace] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  
  const [selectedTrace, setSelectedTrace] = useState<string | null>(null);
  const [traceExplanation, setTraceExplanation] = useState<any>(null);
  const [explainLoading, setExplainLoading] = useState(false);

  const fetchData = async () => {
    setRefreshing(true);
    try {
      const [stRes, rkRes, adRes, esRes, crRes, trRes] = await Promise.all([
        api.get("/stage3/state"),
        api.get("/stage3/risks"),
        api.get("/stage3/adversarial"),
        api.get("/stage3/escalations"),
        api.get("/stage3/corrections"),
        api.get("/stage3/trace")
      ]);
      setState(stRes.data);
      setRisks(rkRes.data);
      setAdv(adRes.data);
      setEscalations(esRes.data);
      setCorrections(crRes.data);
      setTrace(trRes.data);
      setLastUpdate(new Date());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExplain = async (id: string) => {
    setSelectedTrace(id);
    setExplainLoading(true);
    setTraceExplanation(null);
    try {
      const res = await api.get(`/stage3/trace/${id}/explain`);
      setTraceExplanation(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setExplainLoading(false);
    }
  };

  const processCut = async (cut: number) => {
    setRefreshing(true);
    try {
      await api.post(`/stage3/process/${cut}`);
      await fetchData();
    } catch (e) {
      console.error(e);
      setRefreshing(false);
    }
  };

  const processAll = async () => {
    setRefreshing(true);
    try {
      await api.post("/stage3/process_all");
      await fetchData();
    } catch (e) {
      console.error(e);
      setRefreshing(false);
    }
  };

  if (loading) return <div className="p-8 text-zinc-400 animate-pulse">Loading Stage 3 Surveillance...</div>;

  const currentCut = state?.current_cut || 0;
  const cuts = Array.from({ length: 12 }, (_, i) => i + 1);

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-24">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center gap-2">
            <Activity className="text-blue-500" />
            ATLAS SCOPE - STUDY WATCH
          </h1>
          <p className="text-zinc-400 mt-1">Continuous Clinical Surveillance Command Center (Stage 3)</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-zinc-500">Last updated: {lastUpdate.toLocaleTimeString()}</span>
          <button 
            onClick={processAll} 
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium transition-colors"
          >
            {refreshing ? 'Processing...' : 'Run 12-Cut Monitoring'}
          </button>
          <button 
            onClick={fetchData} 
            disabled={refreshing}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded text-sm font-medium transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Overview Top Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#111113] border border-zinc-800 p-4 rounded-xl shadow-lg">
          <p className="text-xs font-bold text-zinc-500 uppercase">System State</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">ACTIVE</span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">Total Records: {state?.total_records}</p>
        </div>
        
        <div className="bg-[#111113] border border-zinc-800 p-4 rounded-xl shadow-lg">
          <p className="text-xs font-bold text-zinc-500 uppercase">Current Cut</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-blue-400">{currentCut}</span>
            <span className="text-sm text-zinc-500">of 12</span>
          </div>
        </div>

        <div className="bg-[#111113] border border-zinc-800 p-4 rounded-xl shadow-lg">
          <p className="text-xs font-bold text-zinc-500 uppercase">Active Risks</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-500">{risks.length}</span>
            <span className="text-sm text-zinc-500">findings</span>
          </div>
        </div>

        <div className="bg-[#111113] border border-zinc-800 p-4 rounded-xl shadow-lg">
          <p className="text-xs font-bold text-zinc-500 uppercase">Budget / Governor</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${state?.budget?.exhausted ? 'text-rose-500' : 'text-emerald-500'}`}>
              {state?.budget?.exhausted ? 'EXHAUSTED' : 'NOMINAL'}
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Consumed: {state?.budget?.consumed} / {state?.budget?.total}
          </p>
        </div>
      </div>

      {/* 1. 12-CUT TIMELINE */}
      <div className="bg-[#111113] border border-zinc-800 rounded-xl shadow-lg p-5">
        <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 mb-4">
          <Clock size={16} /> 12-Cut Surveillance Timeline
        </h2>
        <div className="flex gap-2 w-full justify-between overflow-x-auto pb-2 custom-scrollbar">
          {cuts.map(cut => {
            const isProcessed = state?.processed_cuts?.includes(cut);
            const isCurrent = cut === currentCut;
            return (
              <div 
                key={cut} 
                className={`flex-1 min-w-[80px] border rounded-lg p-3 cursor-pointer transition-all ${
                  isCurrent 
                    ? 'bg-blue-500/10 border-blue-500 text-blue-400' 
                    : isProcessed 
                      ? 'bg-zinc-800/50 border-zinc-700 text-zinc-300 hover:bg-zinc-800' 
                      : 'bg-[#0a0a0c] border-zinc-800/50 text-zinc-600 hover:bg-zinc-900/50'
                }`}
                onClick={() => processCut(cut)}
              >
                <div className="text-[10px] font-bold uppercase text-center mb-1">
                  Cut {cut}
                </div>
                <div className="flex justify-center">
                  {isCurrent ? <Activity size={16} /> : isProcessed ? <CheckCircle2 size={16} /> : <span className="w-4 h-4 rounded-full border border-zinc-700" />}
                </div>
              </div>
            );
          })}
        </div>
        <p className="text-xs text-zinc-500 mt-3 text-center">Click a cut to trigger processing</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 2. RISK & ALERT PANEL */}
        <div className="bg-[#111113] border border-zinc-800 rounded-xl shadow-lg p-5 flex flex-col h-[400px]">
          <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 mb-4">
            <AlertTriangle size={16} className="text-amber-500" /> Risk & Alerts
          </h2>
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-2">
            {risks.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                <ShieldCheck size={32} className="mb-2 text-zinc-600" />
                <p>No active risks detected</p>
              </div>
            ) : (
              risks.map((r, i) => (
                <div key={i} className="border border-zinc-800 bg-[#161618] p-3 rounded-lg flex items-start gap-3">
                  <AlertOctagon size={18} className="text-rose-500 mt-0.5 shrink-0" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold px-1.5 py-0.5 bg-rose-500/20 text-rose-400 rounded">HIGH</span>
                      <span className="text-sm font-bold text-zinc-200">{r.finding_type}</span>
                    </div>
                    {r.scope && <p className="text-xs text-zinc-400 mt-1">Scope: {JSON.stringify(r.scope)}</p>}
                    <p className="text-xs text-zinc-300 mt-1">Action: <span className="font-semibold text-white">{r.recommended_action}</span></p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 5. ADVERSARIAL MONITOR */}
        <div className="bg-[#111113] border border-zinc-800 rounded-xl shadow-lg p-5 flex flex-col h-[400px]">
          <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 mb-4">
            <ShieldAlert size={16} className="text-purple-500" /> Adversarial Monitor
          </h2>
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4">
            {['unit_corruption', 'suspicious_site', 'document_tamper'].map(type => {
              const info = adv?.[type] || { status: 'UNKNOWN', findings: [] };
              const label = type.split('_').map(w => w.toUpperCase()).join(' ');
              const hasFindings = info.findings.length > 0;
              
              return (
                <div key={type} className="border border-zinc-800 bg-zinc-900/30 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-bold text-zinc-300">{label}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${hasFindings ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                      {hasFindings ? 'DETECTED' : 'MONITORING'}
                    </span>
                  </div>
                  {hasFindings ? (
                    <div className="space-y-2 mt-2">
                      {info.findings.map((f: any, i: number) => (
                        <div key={i} className="text-xs bg-black/40 p-2 rounded border border-rose-900/30">
                          <span className="text-rose-400 font-medium">Finding:</span> {f.finding_type} → {f.recommended_action}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-zinc-500 italic">No adversarial signal detected. Evaluating incoming data continuously.</div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 3. CORRECTIONS & AMENDMENTS */}
        <div className="bg-[#111113] border border-zinc-800 rounded-xl shadow-lg p-5 flex flex-col h-[400px]">
          <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 mb-4">
            <GitMerge size={16} className="text-blue-400" /> Corrections Tracker
          </h2>
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3">
            {corrections.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                <Database size={32} className="mb-2 text-zinc-600" />
                <p>No historical corrections processed</p>
              </div>
            ) : (
              corrections.map((c, i) => (
                <div key={i} className="border border-zinc-800 bg-[#161618] p-3 rounded-lg text-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-bold px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded">CUT {c.cut}</span>
                    <span className="font-bold text-zinc-200">Domain: {c.domain}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs mt-1 text-zinc-400">
                    <div>
                      <span className="font-medium text-zinc-500">Record ID:</span><br/>
                      <span className="font-mono text-[10px] break-all">{c.record_id}</span>
                    </div>
                    <div>
                      <span className="font-medium text-zinc-500">Version:</span><br/>
                      v{c.version}
                    </div>
                  </div>
                  <div className="mt-2 text-xs bg-black/40 p-2 rounded text-zinc-300">
                    <span className="text-emerald-400">DAG Invalidated</span> → Targeted Recomputation
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 4. HUMAN ESCALATION */}
        <div className="bg-[#111113] border border-zinc-800 rounded-xl shadow-lg p-5 flex flex-col h-[400px]">
          <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 mb-4">
            <ShieldCheck size={16} className="text-emerald-500" /> Escalation Manager
          </h2>
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-2">
            {escalations.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                <CheckCircle2 size={32} className="mb-2 text-zinc-600" />
                <p>No active escalations</p>
              </div>
            ) : (
              escalations.map((esc, i) => {
                const isStanding = esc.current_state === 'STANDING_LIMITS';
                return (
                  <div key={i} className="border border-zinc-800 bg-[#161618] p-3 rounded-lg text-sm">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-mono text-xs text-blue-400">{esc.escalation_id}</span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                        isStanding ? 'bg-rose-500/20 text-rose-400' 
                        : esc.current_state === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-amber-500/20 text-amber-400'
                      }`}>
                        {esc.current_state}
                      </span>
                    </div>
                    <div className="text-xs text-zinc-400 space-y-1">
                      <p>Created Cut: {esc.created_cut}</p>
                      <p>Unanswered Cuts: <span className={esc.unanswered_cuts >= 4 ? 'text-rose-400 font-bold' : ''}>{esc.unanswered_cuts}</span></p>
                    </div>
                    {isStanding && (
                      <div className="mt-2 text-xs bg-rose-500/10 text-rose-400 p-2 rounded border border-rose-500/20 font-medium">
                        STANDING LIMITS — APPROVAL NOT RECEIVED
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* 6. DECISION TRACE & EXPLAIN */}
      <div className="bg-[#111113] border border-zinc-800 rounded-xl shadow-lg p-5">
        <h2 className="text-sm font-bold text-zinc-300 uppercase tracking-widest flex items-center gap-2 mb-4">
          <Fingerprint size={16} className="text-zinc-400" /> Decision Trace & Immutable Audit
        </h2>
        
        <div className="flex flex-col lg:flex-row gap-6">
          {/* List */}
          <div className="w-full lg:w-1/3 border border-zinc-800 rounded-lg overflow-hidden flex flex-col h-[400px]">
            <div className="bg-zinc-900 px-3 py-2 border-b border-zinc-800 text-xs font-bold text-zinc-400 uppercase">
              Historical Ledger
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              {trace.length === 0 ? (
                <div className="p-4 text-xs text-zinc-500 text-center">No trace decisions recorded.</div>
              ) : (
                trace.map((dec, i) => (
                  <div 
                    key={i} 
                    className={`p-3 border-b border-zinc-800/50 cursor-pointer transition-colors ${selectedTrace === dec.decision_id ? 'bg-blue-500/10 border-l-2 border-l-blue-500' : 'hover:bg-zinc-800/50 border-l-2 border-l-transparent'}`}
                    onClick={() => handleExplain(dec.decision_id)}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-mono font-medium text-zinc-300">{dec.decision_id}</span>
                      <span className="text-[10px] text-zinc-500">Cut {dec.cut}</span>
                    </div>
                    <div className="text-xs text-zinc-400">{dec.decision_type}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Explain Panel */}
          <div className="w-full lg:w-2/3 border border-zinc-800 rounded-lg bg-[#0a0a0c] p-5 h-[400px] overflow-y-auto custom-scrollbar">
            {!selectedTrace ? (
              <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                <FileText size={32} className="mb-2 text-zinc-600" />
                <p>Select a decision to explain</p>
              </div>
            ) : explainLoading ? (
              <div className="text-zinc-400 text-sm animate-pulse">Reconstructing explanation...</div>
            ) : traceExplanation ? (
              <div className="space-y-4">
                <div className="flex items-start justify-between border-b border-zinc-800 pb-3">
                  <div>
                    <h3 className="text-lg font-bold text-white">{traceExplanation.decision_type}</h3>
                    <p className="text-xs font-mono text-zinc-500 mt-1">{traceExplanation.decision_id}</p>
                  </div>
                  <span className="px-2 py-1 bg-zinc-800 text-white text-xs rounded font-bold">
                    ACTION: {traceExplanation.action}
                  </span>
                </div>
                
                <div>
                  <p className="text-xs font-bold text-zinc-500 uppercase mb-2">Rationale</p>
                  <p className="text-sm text-zinc-300 bg-zinc-900/50 p-3 rounded border border-zinc-800">
                    {traceExplanation.why || traceExplanation.what}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-bold text-zinc-500 uppercase">Immutable Evidence Snapshot</p>
                    <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">Historical State</span>
                  </div>
                  <div className="bg-black border border-zinc-800 rounded overflow-x-auto p-3 text-xs font-mono text-zinc-300">
                    <pre>{JSON.stringify(traceExplanation.evidence_snapshot, null, 2)}</pre>
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-2">
                    Note: This evidence snapshot represents the exact state at Cut {traceExplanation.cut}, insulated from any subsequent data corrections.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-rose-400 text-sm">Failed to load explanation</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
