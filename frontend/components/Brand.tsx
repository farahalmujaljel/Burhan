import { Network } from "lucide-react";

export function BrandLogo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative grid h-11 w-11 place-items-center rounded-[18px] bg-gradient-to-br from-blue-600 to-sky-400 text-white shadow-lg shadow-blue-700/20">
        <Network className="h-5 w-5" />
        <span className="absolute -right-1 -top-1 h-3 w-3 rounded-full border-2 border-white bg-blue-300" />
      </div>
      {!compact && (
        <div className="leading-tight">
          <p className="text-lg font-bold tracking-tight text-gray-900">BURHAN</p>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">Research Twin AI</p>
        </div>
      )}
    </div>
  );
}
