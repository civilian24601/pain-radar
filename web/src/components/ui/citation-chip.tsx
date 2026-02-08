"use client";

import { useState, useRef, useEffect } from "react";

interface CitationChipProps {
  index: number;
  url: string;
  excerpt?: string;
}

export function CitationChip({ index, url, excerpt }: CitationChipProps) {
  const [show, setShow] = useState(false);
  const chipRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!show) return;
    function close(e: MouseEvent) {
      if (chipRef.current && !chipRef.current.contains(e.target as Node)) {
        setShow(false);
      }
    }
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [show]);

  return (
    <span ref={chipRef} className="relative inline-block">
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center justify-center rounded bg-indigo-400/10 px-1.5 py-0.5 text-[11px] font-mono text-indigo-400 hover:bg-indigo-400/20 transition-colors cursor-pointer"
        onMouseEnter={() => excerpt && setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={(e) => e.stopPropagation()}
      >
        {index}
      </a>

      {show && excerpt && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 rounded-lg bg-zinc-800 border border-zinc-700 p-2.5 text-xs text-zinc-300 shadow-xl z-50 pointer-events-none">
          <span className="line-clamp-4">&ldquo;{excerpt}&rdquo;</span>
          <span className="block mt-1 text-[10px] text-zinc-500 truncate">
            {url}
          </span>
        </span>
      )}
    </span>
  );
}
