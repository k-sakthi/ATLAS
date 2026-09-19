"use client";

import { useEffect, useState } from "react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import DataTable from "@/components/DataTable";
import EvidencePanel, { EvidenceRecord } from "@/components/EvidencePanel";
import { matchesEvidence } from "@/lib/evidence";
import { AlertOctagon } from "lucide-react";

export default function SAEPage() {
  const { currentCut } = useCut();
  const [data, setData] = useState<any[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: EvidenceRecord[] } | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const res = await api.get(`/analysis/sae?cut=${currentCut}`);
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
    { header: "Term", accessor: "AETERM", sortable: true },
    { header: "Start Date", accessor: "AESTDTC", sortable: true },
    { header: "Severity", accessor: "AESEV", sortable: true, render: (val: any) => <span className="badge badge-amber">{val}</span> },
    { header: "Serious", accessor: "AESER", render: () => <span className="badge badge-red">Yes</span> },
  ];

  const handleViewEvidence = (row: any) => {
    const relevantEvidence = evidenceRecords.filter(e => matchesEvidence(e, { USUBJID: row.USUBJID, AESEQ: row.AESEQ }));
    setSelectedEvidence({
      title: `SAE - ${row.USUBJID}`,
      records: relevantEvidence
    });
  };

  return (
    <div className="space-y-6 fade-in max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <AlertOctagon className="text-orange-500" />
            Serious Adverse Events
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Deterministically identified serious adverse events.</p>
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
