"use client";

import { useEffect, useState } from "react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import DataTable from "@/components/DataTable";
import EvidencePanel, { EvidenceRecord } from "@/components/EvidencePanel";
import { matchesEvidence } from "@/lib/evidence";
import { TestTube } from "lucide-react";

export default function LabsPage() {
  const { currentCut } = useCut();
  const [data, setData] = useState<any[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: EvidenceRecord[] } | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const res = await api.get(`/analysis/labs?cut=${currentCut}`);
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
    { header: "Test Code", accessor: "LBTESTCD", sortable: true },
    { header: "Result", accessor: "LBORRES_NUM", sortable: true, render: (val: any, row: any) => val ? <span className="font-mono text-zinc-300">{val} {row.LBORRESU}</span> : <span className="font-mono text-zinc-300">{row.LBORRES} {row.LBORRESU}</span> },
    { header: "Date", accessor: "LBDTC", sortable: true },
  ];

  const handleViewEvidence = (row: any) => {
    const relevantEvidence = evidenceRecords.filter(e => matchesEvidence(e, { USUBJID: row.USUBJID, LBSEQ: row.LBSEQ }));
    setSelectedEvidence({
      title: `Lab Record - ${row.USUBJID}`,
      records: relevantEvidence
    });
  };

  return (
    <div className="space-y-6 fade-in max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <TestTube className="text-blue-500" />
            Laboratory
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Deterministically filtered laboratory results.</p>
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
