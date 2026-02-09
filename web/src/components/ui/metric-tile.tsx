"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { AnimatedCounter } from "@/components/ui/animated-counter";

const COLOR_MAP = {
  accent: { text: "text-indigo-400", hex: "#818cf8", tw: "indigo-400" },
  green: { text: "text-green-400", hex: "#22c55e", tw: "green-400" },
  yellow: { text: "text-yellow-400", hex: "#eab308", tw: "yellow-400" },
  red: { text: "text-red-400", hex: "#ef4444", tw: "red-400" },
  zinc: { text: "text-zinc-400", hex: "#a1a1aa", tw: "zinc-400" },
} as const;

interface MetricTileProps {
  value: number | string;
  label: string;
  icon: LucideIcon;
  color?: keyof typeof COLOR_MAP;
}

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" as const } },
};

export function MetricTile({
  value,
  label,
  icon: Icon,
  color = "accent",
}: MetricTileProps) {
  const c = COLOR_MAP[color];

  return (
    <motion.div
      variants={fadeUp}
      className="glass-card glass-card-hover p-5 flex flex-col gap-1.5 min-h-[120px] relative overflow-hidden"
    >
      {/* Background glow blob */}
      <div
        className="absolute -top-10 -right-10 w-28 h-28 rounded-full opacity-[0.05]"
        style={{ background: `radial-gradient(circle, ${c.hex}, transparent)` }}
      />

      <Icon size={18} className={`${c.text} opacity-60`} />

      <div className="flex-1 flex flex-col justify-center">
        {typeof value === "number" ? (
          <AnimatedCounter value={value} className={`text-3xl font-bold text-zinc-100`} />
        ) : (
          <span className="text-3xl font-bold text-zinc-100 font-mono tabular-nums">
            {value}
          </span>
        )}
        <span className="text-[11px] text-zinc-500 uppercase tracking-widest mt-1">
          {label}
        </span>
      </div>

      {/* Bottom gradient accent line */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2/5 h-0.5 rounded-full"
        style={{
          background: `linear-gradient(to right, transparent, ${c.hex}40, transparent)`,
        }}
      />
    </motion.div>
  );
}
