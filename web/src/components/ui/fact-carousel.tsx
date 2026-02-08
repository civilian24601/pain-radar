"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const FACTS = [
  "42% of startups fail because they build something nobody needs. Evidence-based validation catches this early.",
  "Reddit alone contains over 2 billion comments. We search the ones most relevant to your pain hypothesis.",
  "The median venture-backed startup spends $1.3M before achieving product-market fit. A $0 evidence scan is the cheapest insurance.",
  "Contradictory evidence is a feature, not a bug. Conflicts in your report highlight where the market is genuinely complex.",
  "Every claim in your report must cite a real source. Our evidence gate rejects hallucinated data and phantom excerpts.",
  "We check job boards and outsourcing posts to gauge whether people already pay to solve this problem.",
  "Your report includes a 7-day validation plan — concrete steps to test the verdict with real users.",
  "Pain signals from reviews (G2, Capterra) often reveal frustrations that polite survey responses miss.",
];

const INTERVAL = 15_000;

export function FactCarousel() {
  const [index, setIndex] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % FACTS.length);
      setProgress(0);
    }, INTERVAL);

    const ticker = setInterval(() => {
      setProgress((prev) => Math.min(prev + 100 / (INTERVAL / 100), 100));
    }, 100);

    return () => {
      clearInterval(timer);
      clearInterval(ticker);
    };
  }, []);

  return (
    <div className="text-center">
      <p className="text-[11px] uppercase tracking-widest text-zinc-600 mb-3">
        Did you know?
      </p>
      <div className="h-16 flex items-center justify-center">
        <AnimatePresence mode="wait">
          <motion.p
            key={index}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.4 }}
            className="text-sm text-zinc-400 max-w-md leading-relaxed"
          >
            {FACTS[index]}
          </motion.p>
        </AnimatePresence>
      </div>
      {/* Progress bar */}
      <div className="mx-auto mt-3 h-0.5 w-32 rounded-full bg-zinc-800 overflow-hidden">
        <div
          className="h-full bg-indigo-400/40 transition-[width] duration-100 ease-linear rounded-full"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
