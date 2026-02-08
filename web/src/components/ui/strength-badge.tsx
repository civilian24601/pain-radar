const STRENGTH_STYLES: Record<string, string> = {
  strong: "bg-green-500/10 text-green-400 border-green-500/20",
  moderate: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  weak: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  none: "bg-zinc-800 text-zinc-500 border-zinc-700/40",
};

interface StrengthBadgeProps {
  strength: string;
}

export function StrengthBadge({ strength }: StrengthBadgeProps) {
  const style = STRENGTH_STYLES[strength] || STRENGTH_STYLES.none;

  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium capitalize ${style}`}
    >
      {strength}
    </span>
  );
}
