"use client";

import { useEffect, useState } from "react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import { 
  Users, AlertOctagon, ShieldAlert, AlertTriangle, 
  ClipboardX, Pill, Ban, FileWarning, Workflow, Activity, Clock
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LineChart, Line
} from "recharts";

export default function Overview() {
  const { currentCut } = useCut();
  const [stats, setStats] = useState({
    subjects: null as number | null,
    hysLaw: null as number | null,
    saes: null as number | null,
    teaes: null as number | null,
    deviations: null as number | null,
    dosing: null as number | null,
    meds: null as number | null,
    exclusions: null as number | null
  });
  
  const [rcStats, setRcStats] = useState({
    escalations: null as number | null,
    queries: null as number | null,
    siteFlags: null as number | null
  });

  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [
          subjRes, hysRes, saeRes, teaeRes, 
          devRes, doseRes, medRes, exclRes,
          escRes, qryRes
        ] = await Promise.allSettled([
          api.get(`/analysis/subjects?cut=${currentCut}`),
          api.get(`/analysis/hys_law?cut=${currentCut}`),
          api.get(`/analysis/sae?cut=${currentCut}`),
          api.get(`/analysis/teae?cut=${currentCut}`),
          api.get(`/analysis/visit_deviations?cut=${currentCut}`),
          api.get(`/analysis/dosing_errors?cut=${currentCut}`),
          api.get(`/analysis/prohibited_meds?cut=${currentCut}`),
          api.get(`/analysis/exclusion_violations?cut=${currentCut}`),
          api.get("/stage2/escalations"),
          api.get("/stage2/queries")
        ]);

        const getCount = (res: PromiseSettledResult<any>) => 
          res.status === "fulfilled" && res.value.data.data ? res.value.data.data.length : null;

        setStats({
          subjects: getCount(subjRes),
          hysLaw: getCount(hysRes),
          saes: getCount(saeRes),
          teaes: getCount(teaeRes),
          deviations: getCount(devRes),
          dosing: getCount(doseRes),
          meds: getCount(medRes),
          exclusions: getCount(exclRes)
        });

        if (escRes.status === "fulfilled") {
          const allEsc = escRes.value.data;
          setRcStats(prev => ({ ...prev, escalations: allEsc.length }));
        }
        if (qryRes.status === "fulfilled") {
          const allQry = qryRes.value.data;
          setRcStats(prev => ({ ...prev, queries: allQry.length }));
        }

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [currentCut]);

  const safetyData = [
    { name: "Hy's Law", count: stats.hysLaw || 0, color: "#ef4444" },
    { name: "SAEs", count: stats.saes || 0, color: "#f97316" },
    { name: "TEAEs", count: stats.teaes || 0, color: "#eab308" }
  ];

  const complianceData = [
    { name: "Deviations", count: stats.deviations || 0, color: "#a855f7" },
    { name: "Dosing", count: stats.dosing || 0, color: "#3b82f6" },
    { name: "Meds", count: stats.meds || 0, color: "#ec4899" },
    { name: "Exclusions", count: stats.exclusions || 0, color: "#f43f5e" }
  ];

  if (!mounted || loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Activity className="animate-spin text-zinc-500" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-8 fade-in pb-10 max-w-6xl mx-auto">
      
      {/* 1. Context */}
      <div className="border-b border-zinc-800 pb-6 mb-8">
        <h1 className="text-3xl font-black tracking-tight text-white mb-2">Study Intelligence</h1>
        <div className="flex items-center gap-6 text-sm text-zinc-400 font-medium">
          <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-500"></div> Protocol ATX-900</span>
          <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-purple-500"></div> Data Cut {currentCut}</span>
          <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500"></div> Deterministic Backend</span>
        </div>
      </div>

      {/* 2. Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#111113] border border-zinc-800 p-5 rounded-xl shadow-sm">
          <div className="text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2"><Users size={14}/> Enrolled Subjects</div>
          <div className="text-3xl font-black text-white">{stats.subjects ?? "-"}</div>
        </div>
        <div className="bg-[#111113] border border-zinc-800 p-5 rounded-xl shadow-sm">
          <div className="text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2"><ShieldAlert size={14}/> Critical Safety Events</div>
          <div className="text-3xl font-black text-red-400">{(stats.hysLaw || 0) + (stats.saes || 0)}</div>
        </div>
        <div className="bg-[#111113] border border-zinc-800 p-5 rounded-xl shadow-sm">
          <div className="text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2"><ClipboardX size={14}/> Protocol Violations</div>
          <div className="text-3xl font-black text-amber-400">{(stats.exclusions || 0) + (stats.deviations || 0)}</div>
        </div>
        <div className="bg-[#111113] border border-zinc-800 p-5 rounded-xl shadow-sm">
          <div className="text-zinc-500 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2"><Workflow size={14}/> Active Escalations</div>
          <div className="text-3xl font-black text-blue-400">{rcStats.escalations ?? "-"}</div>
        </div>
      </div>

      {/* 3. Safety & Findings Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <div className="bg-[#111113] border border-zinc-800 p-6 rounded-xl shadow-sm relative overflow-hidden">
          <h3 className="text-[12px] font-bold text-zinc-400 uppercase tracking-wider mb-6 flex items-center gap-2">
            Safety Signals
          </h3>
          <div className="h-48 w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={safetyData} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                <XAxis type="number" stroke="#71717a" tick={{fill: '#71717a', fontSize: 10}} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#71717a" tick={{fill: '#a1a1aa', fontSize: 11, fontWeight: 500}} axisLine={false} tickLine={false} width={80} />
                <Tooltip cursor={{fill: '#18181b'}} contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '8px' }} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={20}>
                  {safetyData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#111113] border border-zinc-800 p-6 rounded-xl shadow-sm relative overflow-hidden">
          <h3 className="text-[12px] font-bold text-zinc-400 uppercase tracking-wider mb-6 flex items-center gap-2">
            Compliance & Data Quality
          </h3>
          <div className="h-48 w-full relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={complianceData} layout="vertical" margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
                <XAxis type="number" stroke="#71717a" tick={{fill: '#71717a', fontSize: 10}} axisLine={false} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#71717a" tick={{fill: '#a1a1aa', fontSize: 11, fontWeight: 500}} axisLine={false} tickLine={false} width={80} />
                <Tooltip cursor={{fill: '#18181b'}} contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '8px' }} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={20}>
                  {complianceData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* 4. ReviewCrew Activity & Trace Status */}
      <div className="bg-[#111113] border border-zinc-800 rounded-xl p-6 shadow-sm">
        <h3 className="text-[12px] font-bold text-zinc-400 uppercase tracking-wider mb-6 flex items-center gap-2">
          ReviewCrew & System Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-[#09090b] rounded-lg border border-zinc-800/80">
            <div className="text-zinc-400 text-[10px] uppercase font-bold mb-1">Human Gate Queue</div>
            <div className="text-xl font-bold text-amber-400">{rcStats.escalations ?? 0} Pending Actions</div>
            <div className="text-[10px] text-zinc-600 mt-2">Awaiting Monitor Adjudication</div>
          </div>
          <div className="p-4 bg-[#09090b] rounded-lg border border-zinc-800/80">
            <div className="text-zinc-400 text-[10px] uppercase font-bold mb-1">Generated Queries</div>
            <div className="text-xl font-bold text-blue-400">{rcStats.queries ?? 0} Open Queries</div>
            <div className="text-[10px] text-zinc-600 mt-2">Stage 2 Data Manager Output</div>
          </div>
          <div className="p-4 bg-[#09090b] rounded-lg border border-zinc-800/80">
            <div className="text-zinc-400 text-[10px] uppercase font-bold mb-1">Trace Status</div>
            <div className="text-xl font-bold text-green-400 flex items-center gap-2"><Clock size={16}/> Synchronized</div>
            <div className="text-[10px] text-zinc-600 mt-2">Execution Log Validated</div>
          </div>
        </div>
      </div>

    </div>
  );
}
