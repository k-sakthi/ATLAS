"use client";

import { useEffect, useState } from "react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import DataTable from "@/components/DataTable";
import EvidencePanel, { EvidenceRecord } from "@/components/EvidencePanel";
import { matchesEvidence } from "@/lib/evidence";
import { ShieldAlert } from "lucide-react";

export default function SafetyPage() {
  const { currentCut } = useCut();
  const [data, setData] = useState<any[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: EvidenceRecord[] } | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const res = await api.get(`/analysis/hys_law?cut=${currentCut}`);
        setData(res.data.data || []);
        setEvidenceRecords(res.data.evidence?.records || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [currentCut]);

  const columns = [
    { header: "Subject ID", accessor: "USUBJID", sortable: true },
    { 
      header: "Finding", 
      accessor: "finding", 
      render: () => <span className="badge badge-red flex w-max items-center gap-1.5"><ShieldAlert size={10} /> protocol-defined screening signal</span> 
    },
    { 
      header: "Status", 
      accessor: "status", 
      render: () => <span className="text-amber-400 font-semibold text-xs">Medical-monitor adjudication required.</span> 
    },
    { 
      header: "Peak ALT", 
      accessor: "peak_alt", 
      render: (val: any) => val ? <span className="font-mono text-zinc-300">{val.toFixed(2)} U/L</span> : <span className="text-zinc-600">—</span> 
    },
    { 
      header: "Peak AST", 
      accessor: "peak_ast", 
      render: (val: any) => val ? <span className="font-mono text-zinc-300">{val.toFixed(2)} U/L</span> : <span className="text-zinc-600">—</span> 
    },
    { 
      header: "Peak BILI", 
      accessor: "peak_bili", 
      render: (val: any) => val ? <span className="font-mono text-zinc-300">{val.toFixed(2)} mg/dL</span> : <span className="text-zinc-600">—</span> 
    },
  ];

  const handleViewEvidence = (row: any) => {
    const relevantEvidence = evidenceRecords.filter(e => matchesEvidence(e, { USUBJID: row.USUBJID }));
    setSelectedEvidence({
      title: `Hy's Law - ${row.USUBJID}`,
      records: relevantEvidence
    });
  };

  return (
    <div className="space-y-6 fade-in max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <ShieldAlert className="text-red-500" />
            Safety Intelligence
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Protocol-defined screening signals and liver injury monitoring.</p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4 mt-8">
          <div className="skeleton h-12 w-full max-w-sm rounded-lg" />
          <div className="skeleton h-64 w-full rounded-xl" />
        </div>
      ) : (
        <DataTable 
          columns={columns} 
          data={data} 
          onViewEvidence={handleViewEvidence} 
        />
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
