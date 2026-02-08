"use client";

import { useEffect, useState } from "react";

interface ScoreGaugeProps {
  score: number; // 0-5
  max?: number;
  size?: number;
  label?: string;
}

export function ScoreGauge({
  score,
  max = 5,
  size = 48,
  label,
}: ScoreGaugeProps) {
  const [animate, setAnimate] = useState(false);
  const strokeWidth = 4;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const ratio = Math.min(score / max, 1);
  const offset = circumference * (1 - (animate ? ratio : 0));

  // Color gradient based on score
  const color =
    score >= 4
      ? "#22c55e" // green
      : score >= 3
        ? "#818cf8" // indigo
        : score >= 2
          ? "#eab308" // yellow
          : "#ef4444"; // red

  useEffect(() => {
    const t = requestAnimationFrame(() => setAnimate(true));
    return () => cancelAnimationFrame(t);
  }, []);

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#27272a"
          strokeWidth={strokeWidth}
        />
        {/* Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
        />
      </svg>
      <span className="text-sm font-bold text-zinc-200 -mt-[calc(50%+6px)] mb-[calc(50%-6px)]">
        {score}
      </span>
      {label && (
        <span className="text-[10px] text-zinc-500 text-center leading-tight">
          {label}
        </span>
      )}
    </div>
  );
}
