"use client";

import { useEffect, useState } from "react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import DataTable from "@/components/DataTable";
import EvidencePanel, { EvidenceRecord } from "@/components/EvidencePanel";
import { matchesEvidence } from "@/lib/evidence";
import { Ban } from "lucide-react";

export default function ProhibitedMedsPage() {
  const { currentCut } = useCut();
  const [data, setData] = useState<any[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: EvidenceRecord[] } | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const res = await api.get(`/analysis/prohibited_meds?cut=${currentCut}`);
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
    { header: "Medication", accessor: "CMTRT", sortable: true, render: (val: any) => <span className="font-semibold text-pink-400">{val}</span> },
    { header: "Start Date", accessor: "CMSTDTC", sortable: true },
    { header: "End Date", accessor: "CMENDTC", sortable: true },
  ];

  const handleViewEvidence = (row: any) => {
    const relevantEvidence = evidenceRecords.filter(e => matchesEvidence(e, { USUBJID: row.USUBJID, CMSEQ: row.CMSEQ }));
    setSelectedEvidence({
      title: `Prohibited Medication - ${row.USUBJID}`,
      records: relevantEvidence
    });
  };

  return (
    <div className="space-y-6 fade-in max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Ban className="text-pink-500" />
            Prohibited Medications
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Deterministically identified prohibited medications.</p>
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
