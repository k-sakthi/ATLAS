import React from "react";

interface CardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  loading?: boolean;
  severity?: "default" | "danger" | "warning" | "success";
}

const severityMap = {
  default: { border: "border-zinc-800", glow: "" },
  danger: { border: "border-red-900/40", glow: "shadow-[0_0_20px_-4px_rgba(239,68,68,0.1)]" },
  warning: { border: "border-amber-900/40", glow: "shadow-[0_0_20px_-4px_rgba(245,158,11,0.1)]" },
  success: { border: "border-green-900/40", glow: "shadow-[0_0_20px_-4px_rgba(34,197,94,0.1)]" },
};

export default function StatCard({
  title,
  value,
  icon,
  loading,
  severity = "default",
}: CardProps) {
  const s = severityMap[severity];
  return (
    <div
      className={`bg-[#111113] ${s.border} border rounded-xl p-5 transition-all duration-200 hover:border-zinc-700 hover:bg-[#141416] ${s.glow} group`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[12px] font-semibold text-zinc-500 uppercase tracking-wider leading-tight">
          {title}
        </h3>
        {icon && (
          <div className="text-zinc-600 group-hover:text-zinc-500 transition-colors p-1.5 rounded-md bg-zinc-900/50">
            {icon}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-zinc-100 tabular-nums">
        {loading ? (
          <div className="skeleton h-8 w-16" />
        ) : (
          value
        )}
      </div>
    </div>
  );
}
