export type EvidenceRecord = Record<string, any>;

export function normalizeEvidenceRecord(record: any): EvidenceRecord {
  if (!record || typeof record !== "object") return {};

  const rowId = record.row_id && typeof record.row_id === "object" ? record.row_id : {};
  const values = record.values && typeof record.values === "object" ? record.values : {};
  const normalized: EvidenceRecord = {
    ...rowId,
    ...values,
  };

  if (record.file) normalized.file = record.file;
  if (record.rationale) normalized.rationale = record.rationale;

  Object.entries(record).forEach(([key, value]) => {
    if (key !== "row_id" && key !== "values" && normalized[key] === undefined) {
      normalized[key] = value;
    }
  });

  return normalized;
}

export function normalizeEvidence(records: any[] | undefined | null): EvidenceRecord[] {
  return (records || []).map(normalizeEvidenceRecord).filter((record) => Object.keys(record).length > 0);
}

export function evidenceValue(record: any, key: string): any {
  if (!record || typeof record !== "object") return undefined;
  if (record[key] !== undefined) return record[key];
  if (record.row_id && record.row_id[key] !== undefined) return record.row_id[key];
  if (record.values && record.values[key] !== undefined) return record.values[key];
  return undefined;
}

export function matchesEvidence(record: any, criteria: Record<string, any>): boolean {
  return Object.entries(criteria).every(([key, value]) => {
    if (value === undefined || value === null || value === "") return true;
    return String(evidenceValue(record, key)) === String(value);
  });
}
