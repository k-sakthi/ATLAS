"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { GitCompare } from "lucide-react";

export default function ComparePage() {
  const [cutA, setCutA] = useState<number>(4);
  const [cutB, setCutB] = useState<number>(5);
  const availableCuts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13];
  
  const [dataA, setDataA] = useState<any>(null);
  const [dataB, setDataB] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleCompare = async () => {
    setLoading(true);
    try {
      const [resA, resB] = await Promise.all([
        api.get(`/analysis/hys_law?cut=${cutA}`),
        api.get(`/analysis/hys_law?cut=${cutB}`)
      ]);
      setDataA(resA.data.data || []);
      setDataB(resB.data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 fade-in max-w-7xl mx-auto pb-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <GitCompare className="text-blue-500" />
            Cut Comparison
          </h1>
          <p className="text-zinc-400 text-sm mt-1">Compare findings between data cuts.</p>
        </div>
      </div>

      <div className="bg-[#111113] border border-zinc-800 rounded-xl p-6 flex flex-wrap items-end gap-6 shadow-sm">
        <div>
          <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-2">Base Cut</label>
          <select 
            className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm font-semibold rounded-lg p-2.5 w-32 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none cursor-pointer appearance-none pr-8"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2371717a' viewBox='0 0 16 16'%3E%3Cpath d='M4.646 6.646a.5.5 0 0 1 .708 0L8 9.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 8px center",
            }}
            value={cutA}
            onChange={(e) => setCutA(Number(e.target.value))}
          >
            {availableCuts.map(c => <option key={c} value={c}>Cut {c}</option>)}
          </select>
        </div>
        
        <div className="hidden sm:flex text-zinc-600 mb-3 mx-2">
          <GitCompare size={20} />
        </div>

        <div>
          <label className="block text-[11px] text-zinc-500 font-bold uppercase tracking-wider mb-2">Target Cut</label>
          <select 
            className="bg-zinc-900 border border-zinc-700 text-zinc-200 text-sm font-semibold rounded-lg p-2.5 w-32 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none cursor-pointer appearance-none pr-8"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%2371717a' viewBox='0 0 16 16'%3E%3Cpath d='M4.646 6.646a.5.5 0 0 1 .708 0L8 9.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z'/%3E%3C/svg%3E")`,
              backgroundRepeat: "no-repeat",
              backgroundPosition: "right 8px center",
            }}
            value={cutB}
            onChange={(e) => setCutB(Number(e.target.value))}
          >
            {availableCuts.map(c => <option key={c} value={c}>Cut {c}</option>)}
          </select>
        </div>

        <button 
          onClick={handleCompare}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg transition-colors text-sm font-bold shadow-sm disabled:opacity-50"
        >
          {loading ? "Comparing..." : "Compare Cuts"}
        </button>
      </div>

      {!loading && dataA && dataB && (
        <div className="bg-[#111113] border border-zinc-800 rounded-xl overflow-hidden shadow-sm fade-in">
          <div className="p-4 border-b border-zinc-800/80 bg-[#09090b]">
            <h2 className="font-bold text-zinc-100 text-sm">Safety Signals (Hy&apos;s Law) Comparison</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-zinc-800/50">
            <div className="p-6">
              <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-zinc-600"></div>
                Base Cut {cutA}
              </h3>
              {dataA.length > 0 ? (
                <ul className="space-y-3">
                  {dataA.map((item: any, idx: number) => (
                    <li key={idx} className="bg-[#18181b] p-4 rounded-xl border border-zinc-800 text-sm text-zinc-300 flex items-center justify-between group hover:border-zinc-700 transition-colors">
                      <span className="font-bold text-zinc-200">{item.USUBJID}</span>
                      <span className="badge badge-red">Signal</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-8 text-center border border-zinc-800 border-dashed rounded-xl">
                  <p className="text-sm text-zinc-500 font-medium">No signals detected in this cut.</p>
                </div>
              )}
            </div>
            
            <div className="p-6">
              <h3 className="text-xs font-bold text-blue-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                Target Cut {cutB}
              </h3>
              {dataB.length > 0 ? (
                <ul className="space-y-3">
                  {dataB.map((item: any, idx: number) => {
                    const isNew = !dataA.some((a: any) => a.USUBJID === item.USUBJID);
                    return (
                      <li key={idx} className={`bg-[#18181b] p-4 rounded-xl border text-sm text-zinc-300 flex items-center justify-between group transition-colors ${isNew ? 'border-amber-900/40 bg-amber-900/5' : 'border-zinc-800 hover:border-zinc-700'}`}>
                        <span className="font-bold text-zinc-200 flex items-center gap-2">
                          {item.USUBJID}
                          {isNew && <span className="badge badge-amber text-[9px]">New in Cut {cutB}</span>}
                        </span>
                        <span className="badge badge-red">Signal</span>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <div className="p-8 text-center border border-zinc-800 border-dashed rounded-xl">
                  <p className="text-sm text-zinc-500 font-medium">No signals detected in this cut.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
