"use client";

import { useState, useMemo, useCallback } from "react";
import { FileSearch, Search, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

interface Column {
  header: string;
  accessor: string;
  render?: (val: any, row: any) => React.ReactNode;
  sortable?: boolean;
}

interface DataTableProps {
  columns: Column[];
  data: any[];
  onViewEvidence?: (row: any) => void;
  pageSize?: number;
}

export default function DataTable({ columns, data, onViewEvidence, pageSize: defaultPageSize = 10 }: DataTableProps) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const pageSize = defaultPageSize;

  const filteredData = useMemo(() => {
    let result = data;
    if (query) {
      const lowerQuery = query.toLowerCase();
      result = data.filter((row) =>
        columns.some((col) => {
          const val = row[col.accessor];
          return val !== null && val !== undefined && String(val).toLowerCase().includes(lowerQuery);
        })
      );
    }
    if (sortCol) {
      result = [...result].sort((a, b) => {
        const av = a[sortCol] ?? "";
        const bv = b[sortCol] ?? "";
        const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return result;
  }, [data, query, columns, sortCol, sortDir]);

  const pageCount = Math.max(1, Math.ceil(filteredData.length / pageSize));
  const paginatedData = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, page, pageSize]);

  const handleSort = useCallback((accessor: string) => {
    if (sortCol === accessor) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortCol(accessor);
      setSortDir("asc");
    }
    setPage(1);
  }, [sortCol]);

  if (!data || data.length === 0) {
    return (
      <div className="p-10 text-center bg-[#111113] border border-zinc-800 rounded-xl">
        <div className="text-zinc-600 mb-2">
          <FileSearch size={32} className="mx-auto" />
        </div>
        <p className="text-zinc-500 text-sm font-medium">
          No matching deterministic findings were returned for the requested criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#111113] border border-zinc-800 rounded-xl overflow-hidden">
      {/* Toolbar */}
      <div className="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between gap-3">
        <div className="relative w-72">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search records..."
            className="w-full bg-zinc-900/80 border border-zinc-700/60 text-zinc-200 text-sm rounded-lg pl-9 pr-3 py-2 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none placeholder-zinc-600 transition-colors"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <span className="text-[11px] text-zinc-500 font-semibold tabular-nums">
          {filteredData.length} record{filteredData.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="border-b border-zinc-800/80 bg-zinc-900/40">
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 whitespace-nowrap select-none"
                >
                  <button
                    className="flex items-center gap-1 hover:text-zinc-300 transition-colors"
                    onClick={() => handleSort(col.accessor)}
                  >
                    {col.header}
                    {sortCol === col.accessor ? (
                      sortDir === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                    ) : (
                      <ArrowUpDown size={12} className="text-zinc-700" />
                    )}
                  </button>
                </th>
              ))}
              {onViewEvidence && (
                <th className="px-4 py-3 text-[11px] uppercase tracking-wider font-semibold text-zinc-500 text-right">
                  Evidence
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (onViewEvidence ? 1 : 0)}
                  className="px-4 py-10 text-center text-zinc-500 text-sm"
                >
                  No records match your search.
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  className="table-row-hover transition-colors"
                >
                  {columns.map((col, colIdx) => (
                    <td
                      key={colIdx}
                      className="px-4 py-3 whitespace-nowrap text-zinc-300 font-medium"
                    >
                      {col.render
                        ? col.render(row[col.accessor], row)
                        : row[col.accessor] !== null && row[col.accessor] !== undefined
                        ? String(row[col.accessor])
                        : <span className="text-zinc-600">—</span>}
                    </td>
                  ))}
                  {onViewEvidence && (
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => onViewEvidence(row)}
                        className="inline-flex items-center gap-1.5 text-blue-400 hover:text-blue-300 transition-colors text-xs font-semibold bg-blue-500/8 hover:bg-blue-500/15 px-2.5 py-1.5 rounded-md border border-blue-500/20"
                      >
                        <FileSearch size={13} />
                        View
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-4 py-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-500">
        <div className="font-medium tabular-nums">
          {filteredData.length === 0
            ? "0 records"
            : `${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, filteredData.length)} of ${filteredData.length}`}
        </div>
        <div className="flex items-center gap-1">
          <button
            disabled={page === 1}
            onClick={() => setPage(1)}
            className="p-1.5 rounded-md bg-zinc-900 border border-zinc-800 disabled:opacity-30 hover:bg-zinc-800 transition-colors"
            aria-label="First page"
          >
            <ChevronsLeft size={14} />
          </button>
          <button
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
            className="p-1.5 rounded-md bg-zinc-900 border border-zinc-800 disabled:opacity-30 hover:bg-zinc-800 transition-colors"
            aria-label="Previous page"
          >
            <ChevronLeft size={14} />
          </button>
          <span className="px-3 text-zinc-400 font-semibold tabular-nums">
            {page} / {pageCount}
          </span>
          <button
            disabled={page >= pageCount}
            onClick={() => setPage(page + 1)}
            className="p-1.5 rounded-md bg-zinc-900 border border-zinc-800 disabled:opacity-30 hover:bg-zinc-800 transition-colors"
            aria-label="Next page"
          >
            <ChevronRight size={14} />
          </button>
          <button
            disabled={page >= pageCount}
            onClick={() => setPage(pageCount)}
            className="p-1.5 rounded-md bg-zinc-900 border border-zinc-800 disabled:opacity-30 hover:bg-zinc-800 transition-colors"
            aria-label="Last page"
          >
            <ChevronsRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
