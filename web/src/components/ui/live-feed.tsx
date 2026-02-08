"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Activity } from "lucide-react";

export interface FeedEntry {
  id: number;
  text: string;
  time: string; // HH:MM:SS
}

interface LiveFeedProps {
  entries: FeedEntry[];
}

export function LiveFeed({ entries }: LiveFeedProps) {
  // Show most recent 6 entries, newest first
  const visible = entries.slice(-6).reverse();

  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2 text-[11px] uppercase tracking-widest text-zinc-600">
        <Activity size={12} />
        Activity
      </div>
      <div className="h-[140px] overflow-hidden relative">
        <AnimatePresence initial={false}>
          {visible.map((entry, i) => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: i === 0 ? 1 : 0.5, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="text-xs font-mono py-1"
            >
              <span className="text-zinc-600">[{entry.time}]</span>{" "}
              <span className={i === 0 ? "text-zinc-300" : "text-zinc-600"}>
                {entry.text}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
