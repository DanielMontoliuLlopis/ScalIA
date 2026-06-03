import type { ReactNode } from "react";

export function InfoTip({ text }: { text: string }) {
  return (
    <span className="relative inline-flex group align-middle">
      <span className="ml-1 w-3.5 h-3.5 rounded-full bg-gray-300 text-white text-[9px] font-bold flex items-center justify-center cursor-help select-none">
        i
      </span>
      <span className="pointer-events-none absolute left-1/2 bottom-full z-[60] mb-1.5 -translate-x-1/2 w-56 rounded-lg bg-gray-900 text-white text-[11px] font-normal normal-case leading-snug px-2.5 py-2 opacity-0 group-hover:opacity-100 transition-opacity shadow-xl">
        {text}
      </span>
    </span>
  );
}

export function SectionBlock({
  title,
  info,
  action,
  children,
}: {
  title: string;
  info?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-200">
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-2.5 flex items-center justify-between">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center">
          {title}
          {info && <InfoTip text={info} />}
        </h3>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

export function InfoRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-gray-100 last:border-0">
      <span className="text-xs text-gray-400 shrink-0 pt-0.5 w-36">{label}</span>
      <span className={`text-xs text-right text-gray-800 font-medium ${mono ? "font-mono" : ""}`}>
        {value}
      </span>
    </div>
  );
}

export function Chip({ label, highlight = false }: { label: string; highlight?: boolean }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${
        highlight
          ? "bg-violet-50 text-violet-700 border-violet-200"
          : "bg-gray-50 text-gray-600 border-gray-200"
      }`}
    >
      {label}
    </span>
  );
}
