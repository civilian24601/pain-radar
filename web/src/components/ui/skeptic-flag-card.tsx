import { ShieldAlert, AlertTriangle, Info } from "lucide-react";

export type FlagSeverity = "high" | "medium" | "low";

const SEVERITY_CONFIG = {
  high: {
    icon: ShieldAlert,
    border: "border-l-[3px] border-l-red-400",
    bg: "bg-red-500/5 border border-red-500/20",
    iconColor: "text-red-400",
    textColor: "text-zinc-200",
  },
  medium: {
    icon: AlertTriangle,
    border: "border-l-[3px] border-l-amber-400",
    bg: "bg-amber-500/5 border border-amber-500/20",
    iconColor: "text-amber-400",
    textColor: "text-zinc-300",
  },
  low: {
    icon: Info,
    border: "border-l-[3px] border-l-zinc-600",
    bg: "bg-zinc-800/30 border border-zinc-700/30",
    iconColor: "text-zinc-500",
    textColor: "text-zinc-400",
  },
} as const;

const HIGH_PATTERNS = [
  "no evidence", "zero", "missing", "critical", "insufficient",
  "contradiction", "fabricat", "invented", "phantom", "no cited",
  "no citations", "uncited",
];

const MEDIUM_PATTERNS = [
  "limited", "few", "only", "weak", "unclear", "single",
  "one source", "low confidence", "outdated", "old",
];

export function classifyFlagSeverity(flag: string): FlagSeverity {
  const lower = flag.toLowerCase();
  if (HIGH_PATTERNS.some((p) => lower.includes(p))) return "high";
  if (MEDIUM_PATTERNS.some((p) => lower.includes(p))) return "medium";
  return "low";
}

interface SkepticFlagCardProps {
  flag: string;
  severity: FlagSeverity;
}

export function SkepticFlagCard({ flag, severity }: SkepticFlagCardProps) {
  const config = SEVERITY_CONFIG[severity];
  const Icon = config.icon;

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl ${config.bg} ${config.border}`}
    >
      <Icon size={18} className={`${config.iconColor} mt-0.5 shrink-0`} />
      <p className={`text-sm leading-relaxed ${config.textColor}`}>{flag}</p>
    </div>
  );
}
