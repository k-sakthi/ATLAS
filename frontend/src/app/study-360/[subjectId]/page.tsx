"use client";

import { useEffect, useState, useMemo } from "react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import EvidencePanel, { EvidenceRecord } from "@/components/EvidencePanel";
import { matchesEvidence } from "@/lib/evidence";
import DataTable from "@/components/DataTable";
import { 
  User, Activity, AlertTriangle, Pill, FileWarning, ShieldAlert,
  ClipboardX, Calendar, Ban, CheckCircle, Clock, ChevronRight, AlertOctagon, Compass
} from "lucide-react";
import Link from "next/link";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceArea
} from "recharts";

export default function SubjectProfilePage({ params }: { params: { subjectId: string } }) {
  const { currentCut } = useCut();
  const subjectId = params.subjectId;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('Timeline');
  
  const [subjectData, setSubjectData] = useState<any>(null);
  const [timelineEvents, setTimelineEvents] = useState<any[]>([]);
  const [labs, setLabs] = useState<any[]>([]);
  const [aes, setAes] = useState<any[]>([]);
  const [hys, setHys] = useState<any[]>([]);
  const [dose, setDose] = useState<any[]>([]);
  const [meds, setMeds] = useState<any[]>([]);
  const [devs, setDevs] = useState<any[]>([]);
  const [excl, setExcl] = useState<any[]>([]);
  const [monitorHistory, setMonitorHistory] = useState<any[]>([]);
  
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: EvidenceRecord[] } | null>(null);

  useEffect(() => {
    async function fetchAllSubjectData() {
      setLoading(true);
      setError(null);
      try {
        const [
          subjRes, labsRes, aeRes, exRes,
          hysRes, doseRes, devRes, medRes,
          saeRes, teaeRes, exclRes, escRes, qRes
        ] = await Promise.allSettled([
          api.get(`/subjects/${subjectId}?cut=${currentCut}`),
          api.get(`/subjects/${subjectId}/labs?cut=${currentCut}`),
          api.get(`/subjects/${subjectId}/adverse_events?cut=${currentCut}`),
          api.get(`/subjects/${subjectId}/exposure?cut=${currentCut}`),
          api.get(`/analysis/hys_law?cut=${currentCut}`),
          api.get(`/analysis/dosing_errors?cut=${currentCut}`),
          api.get(`/analysis/visit_deviations?cut=${currentCut}`),
          api.get(`/analysis/prohibited_meds?cut=${currentCut}`),
          api.get(`/analysis/sae?cut=${currentCut}`),
          api.get(`/analysis/teae?cut=${currentCut}`),
          api.get(`/analysis/exclusion_violations?cut=${currentCut}`),
          api.get(`/stage2/escalations`),
          api.get(`/stage2/queries`)
        ]);

        if (subjRes.status === 'rejected' || !subjRes.value.data.data) {
          setError("No matching deterministic subject was returned.");
          setLoading(false);
          return;
        }

        const subj = subjRes.value.data.data;
        setSubjectData(subj);

        const extract = (res: PromiseSettledResult<any>) => 
          res.status === 'fulfilled' ? (res.value.data.data || []) : [];
        const extractEv = (res: PromiseSettledResult<any>) => 
          res.status === 'fulfilled' ? (res.value.data.evidence?.records || []) : [];

        const lData = extract(labsRes);
        const aData = extract(aeRes);
        const exData = extract(exRes);
        
        const hData = extract(hysRes).filter((x: any) => x.USUBJID === subjectId);
        const doseErrData = extract(doseRes).filter((x: any) => x.USUBJID === subjectId);
        const devData = extract(devRes).filter((x: any) => x.USUBJID === subjectId);
        const medData = extract(medRes).filter((x: any) => x.USUBJID === subjectId);
        const saeData = extract(saeRes).filter((x: any) => x.USUBJID === subjectId);
        const teaeData = extract(teaeRes).filter((x: any) => x.USUBJID === subjectId);
        const exclData = extract(exclRes).filter((x: any) => x.USUBJID === subjectId);

        setLabs(lData);
        setDose(exData);
        setMeds(medData);
        setDevs(devData);
        setExcl(exclData);

        // Combine AEs
        const aeEv = extractEv(aeRes);
        const allAes = aData.map((ae: any) => {
           const isSae = saeData.some((s: any) => s.AETERM === ae.AETERM);
           const isTeae = teaeData.some((s: any) => s.AETERM === ae.AETERM);
           return { ...ae, isSae, isTeae, evidence: aeEv.filter((e: any) => matchesEvidence(e, { USUBJID: ae.USUBJID, AESEQ: ae.AESEQ })) };
        });
        setAes(allAes);

        // Hys
        const hysEv = extractEv(hysRes).filter((e: any) => matchesEvidence(e, { USUBJID: subjectId }));
        setHys(hData.map((h: any) => ({ ...h, evidence: hysEv })));

        // Timeline mapping
        const events: any[] = [];
        const labsEv = extractEv(labsRes);
        lData.forEach((lab: any) => {
          events.push({
            id: `lab-${lab.LBSEQ}`,
            type: 'Lab',
            date: lab.LBDTC,
            title: `Lab: ${lab.LBTESTCD}`,
            description: `Result: ${lab.LBORRES_NUM ?? lab.LBORRES ?? '-'} ${lab.LBORRESU || ''}`,
            icon: <Activity size={14} className="text-blue-400" />,
            evidence: labsEv.filter((e: any) => matchesEvidence(e, { USUBJID: lab.USUBJID, LBSEQ: lab.LBSEQ }))
          });
        });

        allAes.forEach((ae: any) => {
          events.push({
            id: `ae-${ae.AESEQ}`,
            type: ae.isSae ? 'SAE' : (ae.isTeae ? 'TEAE' : 'AE'),
            date: ae.AESTDTC,
            title: ae.isSae ? 'Serious Adverse Event' : (ae.isTeae ? 'Treatment-Emergent AE' : 'Adverse Event'),
            description: `${ae.AETERM} (Severity: ${ae.AESEV})`,
            icon: <AlertTriangle size={14} className={ae.isSae ? "text-red-500" : "text-yellow-500"} />,
            evidence: ae.evidence
          });
        });

        const exEv = extractEv(exRes);
        exData.forEach((ex: any) => {
          const isErr = doseErrData.some((d: any) => d.VISIT === ex.VISIT);
          events.push({
            id: `ex-${ex.EXSEQ}`,
            type: isErr ? 'Dosing Error' : 'Dosing',
            date: ex.EXSTDTC,
            title: isErr ? 'Dosing Error' : `Dose Administered`,
            description: `${ex.EXDOSE} ${ex.EXDOSU} at ${ex.VISIT}${isErr ? ' (deviation)' : ''}`,
            icon: <Pill size={14} className={isErr ? "text-orange-500" : "text-green-400"} />,
            evidence: exEv.filter((e: any) => matchesEvidence(e, { USUBJID: ex.USUBJID, EXSEQ: ex.EXSEQ }))
          });
        });

        hData.forEach((h: any, i: number) => {
          events.push({
            id: `hys-${i}`,
            type: 'Safety Signal',
            date: h.LBDTC_HEP || h.LBDTC_BILI || "2099-12-31",
            title: `Hy's Law Signal`,
            description: `protocol-defined screening signal. Medical-monitor adjudication required.`,
            icon: <ShieldAlert size={14} className="text-red-500" />,
            evidence: hysEv
          });
        });

        const devEv = extractEv(devRes).filter((e: any) => matchesEvidence(e, { USUBJID: subjectId }));
        devData.forEach((v: any, i: number) => {
          events.push({
            id: `dev-${i}`,
            type: 'Protocol Deviation',
            date: v.VSDTC || v.SVSTDTC,
            title: `Visit Deviation`,
            description: `${v.VISIT} was off by ${Math.abs(v.days || v.deviation_days || 0)} days`,
            icon: <ClipboardX size={14} className="text-purple-400" />,
            evidence: devEv.filter((e: any) => matchesEvidence(e, { USUBJID: v.USUBJID, VSSEQ: v.VSSEQ }))
          });
        });

        const medEv = extractEv(medRes).filter((e: any) => matchesEvidence(e, { USUBJID: subjectId }));
        medData.forEach((m: any, i: number) => {
          events.push({
            id: `med-${i}`,
            type: 'Prohibited Medication',
            date: m.CMSTDTC,
            title: `Prohibited Medication`,
            description: `${m.CMTRT}`,
            icon: <Ban size={14} className="text-pink-400" />,
            evidence: medEv.filter((e: any) => matchesEvidence(e, { USUBJID: m.USUBJID, CMSEQ: m.CMSEQ }))
          });
        });

        const exclEv = extractEv(exclRes).filter((e: any) => matchesEvidence(e, { USUBJID: subjectId }));

        const subjEscalations = escRes.status === 'fulfilled' ? escRes.value.data.filter((e: any) => e.usubjid === subjectId) : [];
        const subjQueries = qRes.status === 'fulfilled' ? qRes.value.data.filter((q: any) => q.usubjid === subjectId) : [];
        
        subjEscalations.forEach((esc: any) => {
            events.push({
                id: `esc-${esc.id}`,
                type: 'Stage 2 Escalation',
                date: "2099-12-31", // Sort to end or top depending
                title: `Escalation: ${esc.code}`,
                description: `Status: ${esc.status} | Monitor: ${esc.monitor_decision || 'Pending'} | ${esc.summary}`,
                icon: <ShieldAlert size={14} className="text-amber-500" />,
                evidence: esc.evidence
            });
        });
        
        subjQueries.forEach((q: any) => {
            events.push({
                id: `q-${q.id}`,
                type: 'Stage 2 Query',
                date: "2099-12-31",
                title: `Data Query`,
                description: `Status: ${q.status} | ${q.text}`,
                icon: <FileWarning size={14} className="text-blue-500" />,
                evidence: q.evidence
            });
        });
        exclData.forEach((ex: any, i: number) => {
          events.push({
            id: `excl-${i}`,
            type: 'Exclusion Violation',
            date: "1900-01-01",
            title: `Exclusion Violation`,
            description: `Violation Reasons: ${(ex.reasons || []).join(', ')}`,
            icon: <FileWarning size={14} className="text-red-500" />,
            evidence: exclEv
          });
        });

        events.sort((a, b) => {
          const dateA = a.date ? new Date(a.date).getTime() : 0;
          const dateB = b.date ? new Date(b.date).getTime() : 0;
          return dateA - dateB;
        });

        setTimelineEvents(events);
      } catch (err) {
        console.error(err);
        setError("An error occurred while fetching subject data.");
      } finally {
        setLoading(false);
      }
    }

    fetchAllSubjectData();
  }, [subjectId, currentCut]);

  const labChartData = useMemo(() => {
    const dates = Array.from(new Set(labs.filter(l => l.LBDTC).map(l => l.LBDTC))).sort();
    return dates.map(date => {
      const point: any = { name: date };
      labs.filter(l => l.LBDTC === date).forEach(l => {
        if (l.LBTESTCD === 'ALT' || l.LBTESTCD === 'AST' || l.LBTESTCD === 'BILI' || l.LBTESTCD === 'GLUC') {
          point[l.LBTESTCD] = l.LBORRES_NUM;
        }
      });
      return point;
    });
  }, [labs]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 border-4 border-purple-500/20 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          <Compass className="absolute inset-0 m-auto text-purple-400 opacity-50" size={24} />
        </div>
        <div className="text-zinc-400 font-medium animate-pulse">Constructing Study 360° Profile...</div>
      </div>
    );
  }

  if (error || !subjectData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-5 fade-in">
        <div className="p-5 bg-red-500/10 rounded-full border border-red-500/20">
          <AlertTriangle size={40} className="text-red-500" />
        </div>
        <div className="text-xl text-zinc-200 font-bold tracking-tight">{error || "Data unavailable"}</div>
        <Link href="/study-360" className="mt-4 text-blue-400 hover:text-blue-300 hover:underline font-medium transition-colors">
          Return to Subject Explorer
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-20 fade-in">
      {/* Subject Header */}
      <div className="bg-[#111113] border border-zinc-800/80 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/5 rounded-full blur-[80px] -mr-32 -mt-32 pointer-events-none"></div>
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 relative z-10">
          <div className="flex items-center gap-6">
            <div className="bg-[#09090b] p-5 rounded-2xl border border-zinc-800 shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]">
              <User size={36} className="text-purple-400" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h1 className="text-3xl font-extrabold tracking-tight text-white font-mono">{subjectData.USUBJID}</h1>
                <span className="badge badge-purple px-2 py-1 text-[11px]">Protocol 042-S01</span>
                <span className="badge badge-gray px-2 py-1 text-[11px]">Cut {currentCut}</span>
              </div>
              <p className="text-zinc-400 text-sm font-medium flex items-center gap-2">
                <span className="flex items-center gap-1.5"><strong className="text-zinc-300">Site:</strong> {subjectData.SITEID}</span>
                <span className="text-zinc-700">&bull;</span>
                <span className="flex items-center gap-1.5"><strong className="text-zinc-300">Arm:</strong> {subjectData.ARM}</span>
                <span className="text-zinc-700">&bull;</span>
                <span className="flex items-center gap-1.5">
                  <strong className="text-zinc-300">Status:</strong> 
                  <span className={subjectData.DSDECOD === 'COMPLETED' ? 'text-green-400' : 'text-zinc-300'}>{subjectData.DSDECOD}</span>
                </span>
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-8 gap-y-4 text-sm bg-zinc-900/50 p-5 rounded-xl border border-zinc-800/60 flex-shrink-0">
            <div>
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Demographics</span>
              <div className="text-zinc-200 font-semibold">{subjectData.AGE} yrs / {subjectData.SEX}</div>
            </div>
            <div>
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Screening</span>
              <div className="text-zinc-200 font-semibold font-mono text-[13px]">{subjectData.RFSTDTC || "N/A"}</div>
            </div>
            <div>
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">Enrolled</span>
              <div className="text-zinc-200 font-semibold">{subjectData.ENROLYN === 'Y' ? <span className="text-green-400">Yes</span> : 'No'}</div>
            </div>
            <div>
              <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider block mb-1">End of Study</span>
              <div className="text-zinc-200 font-semibold font-mono text-[13px]">{subjectData.RFENDTC || "N/A"}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-zinc-800/80 pb-px overflow-x-auto no-scrollbar pt-2">
        {[
          { name: 'Timeline', count: timelineEvents.length },
          { name: 'Safety', count: hys.length + aes.length, alert: hys.length > 0 || aes.some(a => a.isSae) },
          { name: 'Laboratories', count: labs.length },
          { name: 'Exposure', count: dose.length + meds.length },
          { name: 'Deviations & Exclusions', count: devs.length + excl.length, alert: excl.length > 0 }
        ].map(tab => (
          <button
            key={tab.name}
            onClick={() => setActiveTab(tab.name)}
            className={`flex items-center gap-2 px-5 py-3 text-[13px] font-bold whitespace-nowrap border-b-2 transition-all ${
              activeTab === tab.name 
                ? 'border-purple-500 text-purple-400 bg-purple-500/10 rounded-t-lg' 
                : 'border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 rounded-t-lg'
            }`}
          >
            {tab.name}
            <span className={`px-2 py-0.5 rounded-full text-[10px] ${
              activeTab === tab.name ? 'bg-purple-500/20 text-purple-300' : 'bg-zinc-800 text-zinc-400'
            }`}>
              {tab.count}
            </span>
            {tab.alert && <div className="w-1.5 h-1.5 rounded-full bg-red-500 ml-1"></div>}
          </button>
        ))}
      </div>

      <div className="pt-2">
        {/* TIMELINE TAB */}
        {activeTab === 'Timeline' && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
                <Clock className="text-purple-400" size={20} />
                Chronological Study Journey
              </h2>
            </div>
            
            {timelineEvents.length === 0 ? (
              <div className="text-zinc-500 text-sm p-12 text-center bg-[#111113] border border-zinc-800 rounded-2xl">
                No events found for this subject at Cut {currentCut}.
              </div>
            ) : (
              <div className="relative border-l-2 border-zinc-800 ml-4 md:ml-8 pl-8 md:pl-12 space-y-10 py-4">
                {timelineEvents.map((evt, idx) => (
                  <div key={evt.id} className="relative group">
                    {/* Timeline Node */}
                    <div className="absolute -left-[43px] md:-left-[59px] top-1 bg-[#09090b] border-[3px] border-zinc-800 p-1.5 rounded-full z-10 group-hover:border-purple-500 transition-colors shadow-lg">
                      {evt.icon}
                    </div>
                    
                    {/* Event Card */}
                    <div className="bg-[#111113] border border-zinc-800/80 rounded-2xl p-5 hover:border-zinc-600 transition-all shadow-sm hover:shadow-xl group-hover:-translate-y-0.5 duration-200">
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3">
                        <div>
                          <div className="flex items-center gap-3 mb-1.5">
                            <span className="text-[10px] font-bold px-2 py-0.5 bg-zinc-900 text-zinc-400 rounded-md border border-zinc-800 uppercase tracking-widest">
                              {evt.type}
                            </span>
                            <span className="flex items-center gap-1.5 text-[11px] text-zinc-500 font-mono font-semibold bg-zinc-900/50 px-2 py-0.5 rounded-full border border-zinc-800/50">
                              <Calendar size={12} />
                              {evt.date || "Unknown Date"}
                            </span>
                          </div>
                          <h3 className="font-bold text-zinc-100 text-[15px]">{evt.title}</h3>
                        </div>
                      </div>
                      
                      <p className="text-[13px] text-zinc-400 mb-5 font-medium leading-relaxed">{evt.description}</p>
                      
                      {evt.evidence && evt.evidence.length > 0 && (
                        <button 
                          onClick={() => setSelectedEvidence({ title: evt.title, records: evt.evidence })}
                          className="text-[11px] font-bold text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1.5 bg-blue-900/10 px-3 py-1.5 rounded-lg border border-blue-900/30 hover:bg-blue-900/20 w-max"
                        >
                          <CheckCircle size={14} />
                          Trace Evidence
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SAFETY TAB */}
        {activeTab === 'Safety' && (
          <div className="space-y-8 fade-in">
            <section>
              <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                <ShieldAlert className="text-red-500" size={20} />
                Safety Signals (Hy&apos;s Law)
              </h2>
              {hys.length === 0 ? (
                <div className="text-zinc-500 text-sm p-6 bg-[#111113] border border-zinc-800 rounded-xl text-center font-medium">No liver safety signals detected.</div>
              ) : (
                <div className="grid gap-4">
                  {hys.map((h, i) => (
                    <div key={i} className="bg-red-950/10 border border-red-900/30 p-5 rounded-xl relative overflow-hidden flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="absolute top-0 left-0 w-1 h-full bg-red-500"></div>
                      <div>
                        <h3 className="text-red-400 font-bold text-sm mb-1 flex items-center gap-2">
                          <AlertOctagon size={16} /> protocol-defined screening signal
                        </h3>
                        <p className="text-red-300/70 text-xs font-semibold uppercase tracking-wider">Medical-monitor adjudication required.</p>
                      </div>
                      <button onClick={() => setSelectedEvidence({ title: "Hy's Law Signal", records: h.evidence })} className="text-[11px] font-bold text-red-400 bg-red-950/40 px-4 py-2 rounded-lg border border-red-900/40 hover:bg-red-900/40 transition-colors whitespace-nowrap">Trace Evidence</button>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                <AlertTriangle className="text-amber-500" size={20} />
                Adverse Events
              </h2>
              <DataTable 
                columns={[
                  { header: "Term", accessor: "AETERM", sortable: true },
                  { header: "Date", accessor: "AESTDTC", sortable: true, render: (val: any) => <span className="font-mono text-zinc-400">{val}</span> },
                  { header: "Severity", accessor: "AESEV", sortable: true, render: (val: any) => <span className="badge badge-gray">{val}</span> },
                  { header: "Flags", accessor: "flags", render: (_, row: any) => (
                    <div className="flex gap-2">
                      {row.isSae && <span className="badge badge-red">SAE</span>}
                      {row.isTeae && <span className="badge badge-amber">TEAE</span>}
                      {!row.isSae && !row.isTeae && <span className="text-zinc-600">—</span>}
                    </div>
                  )}
                ]} 
                data={aes} 
                onViewEvidence={(row) => setSelectedEvidence({ title: "AE Evidence", records: row.evidence })}
              />
            </section>
          </div>
        )}

        {/* LABORATORIES TAB */}
        {activeTab === 'Laboratories' && (
          <div className="space-y-8 fade-in">
            <h2 className="text-lg font-bold text-zinc-100 flex items-center gap-2">
              <Activity className="text-blue-400" size={20} />
              Laboratory Profile
            </h2>
            
            {labChartData.length > 0 && (
              <div className="bg-[#111113] p-6 rounded-2xl border border-zinc-800 shadow-sm relative overflow-hidden">
                <h3 className="text-[12px] font-bold text-zinc-400 uppercase tracking-wider mb-6 relative z-10 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  Key Biomarker Trends (Liver Panel)
                </h3>
                <div className="h-80 w-full relative z-10">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={labChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                      <XAxis dataKey="name" stroke="#71717a" tick={{fill: '#71717a', fontSize: 11, fontWeight: 500}} axisLine={{ stroke: '#3f3f46' }} tickLine={false} dy={10} />
                      <YAxis stroke="#71717a" tick={{fill: '#71717a', fontSize: 11}} axisLine={false} tickLine={false} dx={-10} />
                      <Tooltip 
                        contentStyle={{backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px', color: '#fff', fontSize: '12px', fontWeight: 500}} 
                        itemStyle={{ padding: '2px 0' }}
                      />
                      <Legend wrapperStyle={{paddingTop: '20px', fontSize: '12px', fontWeight: 500}} iconType="circle" />
                      <Line type="monotone" dataKey="ALT" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, strokeWidth: 0, fill: '#3b82f6'}} activeDot={{r: 6}} connectNulls />
                      <Line type="monotone" dataKey="AST" stroke="#a855f7" strokeWidth={3} dot={{r: 4, strokeWidth: 0, fill: '#a855f7'}} activeDot={{r: 6}} connectNulls />
                      <Line type="monotone" dataKey="BILI" stroke="#f59e0b" strokeWidth={3} dot={{r: 4, strokeWidth: 0, fill: '#f59e0b'}} activeDot={{r: 6}} connectNulls />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            <DataTable 
              columns={[
                { header: "Date", accessor: "LBDTC", sortable: true, render: (val: any) => <span className="font-mono text-zinc-400">{val}</span> },
                { header: "Test Code", accessor: "LBTESTCD", sortable: true, render: (val: any) => <span className="font-bold text-zinc-200">{val}</span> },
                { header: "Result", accessor: "LBORRES_NUM", sortable: true, render: (val: any, row: any) => val ? <span className="font-mono text-zinc-200 font-medium">{val} {row.LBORRESU}</span> : <span className="font-mono text-zinc-200 font-medium">{row.LBORRES} {row.LBORRESU}</span> },
                { header: "Ref Range", accessor: "LBORNRLO", render: (_, row: any) => <span className="text-zinc-500 font-mono text-[13px]">{row.LBORNRLO || '-'} &mdash; {row.LBORNRHI || '-'}</span> },
              ]} 
              data={labs} 
              onViewEvidence={(row) => setSelectedEvidence({ title: `Lab ${row.LBTESTCD}`, records: [row] })}
            />
          </div>
        )}

        {/* EXPOSURE TAB */}
        {activeTab === 'Exposure' && (
          <div className="space-y-8 fade-in">
            <section>
              <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                <Pill className="text-blue-400" size={20} />
                Dosing Administration
              </h2>
              <DataTable 
                columns={[
                  { header: "Visit", accessor: "VISIT", sortable: true },
                  { header: "Date", accessor: "EXSTDTC", sortable: true, render: (val: any) => <span className="font-mono text-zinc-400">{val}</span> },
                  { header: "Dose", accessor: "EXDOSE", sortable: true, render: (val: any, row: any) => <span className="font-mono font-bold text-blue-400">{val} {row.EXDOSU}</span> },
                  { header: "Treatment", accessor: "EXTRT", sortable: true },
                ]} 
                data={dose} 
              />
            </section>
            
            <section>
              <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                <Ban className="text-pink-400" size={20} />
                Prohibited Medications
              </h2>
              {meds.length === 0 ? (
                <div className="text-zinc-500 text-sm p-6 bg-[#111113] border border-zinc-800 rounded-xl text-center font-medium">No prohibited medications recorded.</div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {meds.map((m, i) => (
                    <div key={i} className="bg-[#111113] border border-pink-900/30 p-5 rounded-xl flex flex-col justify-between gap-4 group hover:border-pink-900/60 transition-colors shadow-sm">
                      <div>
                        <h3 className="text-pink-400 font-bold text-[15px] mb-1">{m.CMTRT}</h3>
                        <p className="text-zinc-400 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5"><Calendar size={12}/> Started: <span className="font-mono text-zinc-300">{m.CMSTDTC}</span></p>
                      </div>
                      <button onClick={() => setSelectedEvidence({ title: "Medication Evidence", records: [m] })} className="text-[11px] font-bold text-blue-400 bg-blue-900/10 px-3 py-1.5 rounded-lg border border-blue-900/30 hover:bg-blue-900/20 transition-colors w-max">Trace Evidence</button>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {/* DEVIATIONS & EXCLUSIONS TAB */}
        {activeTab === 'Deviations & Exclusions' && (
          <div className="space-y-8 fade-in">
            <section>
              <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                <ClipboardX className="text-purple-400" size={20} />
                Visit Deviations
              </h2>
              {devs.length === 0 ? (
                <div className="text-zinc-500 text-sm p-6 bg-[#111113] border border-zinc-800 rounded-xl text-center font-medium">No visit deviations detected.</div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {devs.map((v, i) => (
                    <div key={i} className="bg-[#111113] border border-zinc-800 p-5 rounded-xl flex flex-col justify-between gap-4 group hover:border-zinc-700 transition-colors shadow-sm">
                      <div>
                        <h3 className="text-zinc-200 font-bold text-[15px] mb-1">{v.VISIT}</h3>
                        <p className="text-purple-400 text-xs font-semibold uppercase tracking-wider">Off by {Math.abs(v.days || v.deviation_days || 0)} days</p>
                      </div>
                      <button onClick={() => setSelectedEvidence({ title: "Deviation Evidence", records: [v] })} className="text-[11px] font-bold text-blue-400 bg-blue-900/10 px-3 py-1.5 rounded-lg border border-blue-900/30 hover:bg-blue-900/20 transition-colors w-max">Trace Evidence</button>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2 className="text-lg font-bold text-zinc-100 mb-4 flex items-center gap-2">
                <FileWarning className="text-red-500" size={20} />
                Exclusion Violations
              </h2>
              {excl.length === 0 ? (
                <div className="text-zinc-500 text-sm p-6 bg-[#111113] border border-zinc-800 rounded-xl text-center font-medium">No exclusion violations.</div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {excl.map((ex, i) => (
                    <div key={i} className="bg-red-950/10 border border-red-900/30 p-5 rounded-xl flex flex-col justify-between gap-4 group hover:border-red-900/50 transition-colors">
                      <div>
                        <h3 className="text-red-400 font-bold text-sm mb-1 uppercase tracking-wider">Protocol Violation</h3>
                        <p className="text-zinc-300 text-sm font-medium leading-relaxed">Reasons: {(ex.reasons || []).join(', ')}</p>
                      </div>
                      <button onClick={() => setSelectedEvidence({ title: "Exclusion Evidence", records: [ex] })} className="text-[11px] font-bold text-red-400 bg-red-950/40 px-3 py-1.5 rounded-lg border border-red-900/40 hover:bg-red-900/40 transition-colors w-max">Trace Evidence</button>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </div>

      <EvidencePanel 
        isOpen={!!selectedEvidence} 
        onClose={() => setSelectedEvidence(null)} 
        title={selectedEvidence?.title || ""} 
        evidence={selectedEvidence?.records || []} 
      />
    </div>
  );
}

