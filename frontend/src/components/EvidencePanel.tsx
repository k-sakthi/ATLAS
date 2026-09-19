"use client";

import { X, Copy, Check } from "lucide-react";
import { useEffect, useState, useCallback } from "react";
import { normalizeEvidence } from "@/lib/evidence";

export interface EvidenceRecord {
  [key: string]: any;
}

interface EvidencePanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  evidence: EvidenceRecord[];
  emptyMessage?: string;
}

export default function EvidencePanel({ isOpen, onClose, title, evidence, emptyMessage }: EvidencePanelProps) {
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const displayEvidence = normalizeEvidence(evidence);

  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape" && isOpen) {
      onClose();
    }
  }, [isOpen, onClose]);

  useEffect(() => {
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [handleEscape]);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (!isOpen) return null;

  return (
    <>
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 fade-in"
        onClick={onClose}
      />
      <div className="fixed top-0 right-0 w-[500px] max-w-[90vw] h-screen bg-[#111113] border-l border-zinc-800 shadow-2xl flex flex-col z-50 overflow-hidden slide-in-right">
        <div className="p-5 border-b border-zinc-800/80 flex items-center justify-between bg-[#09090b]">
          <div>
            <h2 className="font-bold text-lg text-zinc-100 tracking-tight">Evidence Source</h2>
            <p className="text-xs text-zinc-500 font-medium mt-0.5">{title}</p>
          </div>
          <button 
            onClick={onClose} 
            className="text-zinc-500 hover:text-zinc-300 bg-zinc-900 hover:bg-zinc-800 p-2 rounded-md transition-colors"
            aria-label="Close panel"
          >
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {displayEvidence.length > 0 ? (
            displayEvidence.map((record, idx) => {
              const hasConversion = record.S07_CONVERSION_APPLIED === "YES";
              
              return (
                <div key={idx} className="bg-[#18181b] border border-zinc-800/80 rounded-xl overflow-hidden shadow-sm">
                  <div className="bg-zinc-900/50 px-4 py-2.5 border-b border-zinc-800/80 flex items-center justify-between">
                    <div className="text-[11px] text-zinc-400 font-bold uppercase tracking-wider">
                      Record {idx + 1}
                    </div>
                    {hasConversion && (
                      <span className="badge badge-purple">S07 Converted</span>
                    )}
                  </div>
                  <dl className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                    {Object.entries(record).map(([key, val]) => (
                      <div key={key} className="col-span-1 group relative">
                        <dt className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-1 truncate">{key}</dt>
                        <dd className="text-zinc-200 font-mono text-[13px] break-all bg-zinc-900/30 p-2 rounded border border-zinc-800/50 group-hover:border-zinc-700 transition-colors">
                          {val !== null && val !== undefined ? (typeof val === "object" ? JSON.stringify(val) : String(val)) : <span className="text-zinc-600">—</span>}
                          
                          {val !== null && val !== undefined && (
                            <button 
                              onClick={() => copyToClipboard(typeof val === "object" ? JSON.stringify(val) : String(val), `${idx}-${key}`)}
                              className="absolute top-7 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 bg-zinc-800 hover:bg-zinc-700 rounded text-zinc-400"
                              title="Copy value"
                            >
                              {copiedKey === `${idx}-${key}` ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
                            </button>
                          )}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              );
            })
          ) : (
            <div className="text-center p-8 bg-[#18181b] border border-zinc-800 border-dashed rounded-xl">
              <p className="text-zinc-500 text-sm font-medium">{emptyMessage || "No deterministic evidence was returned for this finding."}</p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
