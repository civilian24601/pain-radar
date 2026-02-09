import type { LucideIcon } from "lucide-react";

const COLOR_MAP = {
  accent: { bg: "bg-indigo-400/10", text: "text-indigo-400", grad: "#818cf8" },
  green: { bg: "bg-green-400/10", text: "text-green-400", grad: "#22c55e" },
  yellow: { bg: "bg-yellow-400/10", text: "text-yellow-400", grad: "#eab308" },
  red: { bg: "bg-red-400/10", text: "text-red-400", grad: "#ef4444" },
  orange: { bg: "bg-orange-400/10", text: "text-orange-400", grad: "#f97316" },
} as const;

interface SectionHeaderProps {
  icon: LucideIcon;
  title: string;
  subtitle?: string;
  count?: number;
  color?: keyof typeof COLOR_MAP;
}

export function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  count,
  color = "accent",
}: SectionHeaderProps) {
  const c = COLOR_MAP[color];

  return (
    <div className="mb-5">
      <div className="flex items-center gap-3">
        <div
          className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center shrink-0`}
        >
          <Icon size={16} className={c.text} />
        </div>
        <div className="flex items-baseline gap-3">
          <h2 className="text-xl font-semibold text-zinc-100">{title}</h2>
          {count !== undefined && (
            <span className="text-sm text-zinc-500 font-mono">{count}</span>
          )}
          {subtitle && (
            <span className="text-sm text-zinc-500">{subtitle}</span>
          )}
        </div>
      </div>
      {/* Gradient underline */}
      <div
        className="mt-2.5 ml-11 h-0.5 w-12 rounded-full"
        style={{
          background: `linear-gradient(to right, ${c.grad}, transparent)`,
        }}
      />
    </div>
  );
}
