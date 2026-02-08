"use client";

import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface ScanAnimationProps {
  citationsFound: number;
}

// Deterministic pseudo-random positions for blips based on index
function blipPosition(i: number) {
  const angle = ((i * 137.508) % 360) * (Math.PI / 180); // golden angle
  const r = 20 + ((i * 31) % 70); // radius 20-90
  const x = 120 + Math.cos(angle) * r;
  const y = 120 + Math.sin(angle) * r;
  return { x, y };
}

export function ScanAnimation({ citationsFound }: ScanAnimationProps) {
  // Cap visual blips at 40 to avoid clutter
  const blipCount = Math.min(citationsFound, 40);

  const blips = useMemo(() => {
    return Array.from({ length: blipCount }, (_, i) => ({
      id: i,
      ...blipPosition(i),
    }));
  }, [blipCount]);

  return (
    <div className="relative flex items-center justify-center">
      <svg
        width="240"
        height="240"
        viewBox="0 0 240 240"
        fill="none"
        className="opacity-90"
      >
        {/* Grid rings */}
        <circle cx="120" cy="120" r="100" stroke="#27272a" strokeWidth="1" />
        <circle cx="120" cy="120" r="70" stroke="#27272a" strokeWidth="1" />
        <circle cx="120" cy="120" r="40" stroke="#27272a" strokeWidth="1" />

        {/* Crosshairs */}
        <line x1="120" y1="18" x2="120" y2="222" stroke="#27272a" strokeWidth="0.5" />
        <line x1="18" y1="120" x2="222" y2="120" stroke="#27272a" strokeWidth="0.5" />

        {/* Sweep trail (conic gradient faked with a semi-transparent arc) */}
        <defs>
          <linearGradient id="sweep-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#818cf8" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#818cf8" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Sweep group — rotates */}
        <g
          style={{
            transformOrigin: "120px 120px",
            animation: "radar-sweep 4s linear infinite",
          }}
        >
          {/* Sweep line */}
          <line
            x1="120"
            y1="120"
            x2="120"
            y2="22"
            stroke="#818cf8"
            strokeWidth="2"
            strokeLinecap="round"
          />
          {/* Sweep trail wedge */}
          <path
            d="M120,120 L120,22 A98,98 0 0,0 51,55 Z"
            fill="url(#sweep-grad)"
            opacity="0.4"
          />
        </g>

        {/* Center dot */}
        <circle cx="120" cy="120" r="3" fill="#818cf8" />

        {/* Blips */}
        <AnimatePresence>
          {blips.map((blip) => (
            <motion.circle
              key={blip.id}
              cx={blip.x}
              cy={blip.y}
              r="3"
              fill="#818cf8"
              initial={{ scale: 0, opacity: 0 }}
              animate={{
                scale: 1,
                opacity: blip.id < blipCount - 10 ? 0.35 : 0.9,
              }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              style={{
                filter: "drop-shadow(0 0 4px rgba(129, 140, 248, 0.6))",
              }}
            />
          ))}
        </AnimatePresence>
      </svg>
    </div>
  );
}
