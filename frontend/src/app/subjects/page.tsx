"use client";

import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import { useCut } from "@/components/CutContext";
import { api } from "@/lib/api";
import DataTable from "@/components/DataTable";
import EvidencePanel, { EvidenceRecord } from "@/components/EvidencePanel";
import { matchesEvidence } from "@/lib/evidence";

export default function SubjectsPage() {
  const { currentCut } = useCut();
  const [data, setData] = useState<any[]>([]);
  const [evidenceRecords, setEvidenceRecords] = useState<EvidenceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEvidence, setSelectedEvidence] = useState<{ title: string; records: EvidenceRecord[] } | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const res = await api.get(`/analysis/subjects?cut=${currentCut}`);
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
    { header: "Site", accessor: "SITEID", sortable: true },
    { header: "Country", accessor: "COUNTRY", sortable: true },
    { header: "Age", accessor: "AGE", sortable: true },
    { header: "Sex", accessor: "SEX", sortable: true },
    { header: "Arm", accessor: "ARM", sortable: true },
    { header: "First Dose", accessor: "RFSTDTC", sortable: true },
    {
      header: "Screening HbA1c",
      accessor: "SCR_HBA1C",
      sortable: true,
      render: (val: any) => val !== null && val !== undefined
        ? <span className="font-mono text-zinc-300">{val}</span>
        : <span className="text-zinc-600">-</span>,
    },
  ];

  const handleViewEvidence = (row: any) => {
    const relevantEvidence = evidenceRecords.filter(e => matchesEvidence(e, { USUBJID: row.USUBJID }));
    setSelectedEvidence({
      title: `Subject Record - ${row.USUBJID}`,
      records: relevantEvidence,
    });
  };

  return (
    <div className="space-y-6 fade-in max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users className="text-blue-500" />
            Subjects
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Current subject roster from the deterministic data cut.</p>
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
