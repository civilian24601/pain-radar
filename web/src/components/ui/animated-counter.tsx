"use client";

import { useEffect, useRef, useState } from "react";

interface AnimatedCounterProps {
  value: number;
  className?: string;
  duration?: number;
}

export function AnimatedCounter({
  value,
  className = "",
  duration = 600,
}: AnimatedCounterProps) {
  const [display, setDisplay] = useState(value);
  const prevRef = useRef(value);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    const from = prevRef.current;
    const to = value;
    if (from === to) return;

    const start = performance.now();

    function tick(now: number) {
      const t = Math.min((now - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(from + (to - from) * eased));

      if (t < 1) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        prevRef.current = to;
      }
    }

    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  return (
    <span className={`font-mono tabular-nums ${className}`}>{display}</span>
  );
}
