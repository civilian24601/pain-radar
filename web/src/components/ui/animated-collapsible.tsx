"use client";

import { type ReactNode, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight } from "lucide-react";

interface AnimatedCollapsibleProps {
  title: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
}

export function AnimatedCollapsible({
  title,
  defaultOpen = false,
  children,
  className = "",
}: AnimatedCollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={className}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-5 py-3.5 font-medium text-zinc-200 hover:text-zinc-100 transition-colors select-none text-left"
      >
        <motion.span
          animate={{ rotate: open ? 90 : 0 }}
          transition={{ duration: 0.2 }}
          className="inline-flex text-zinc-500"
        >
          <ChevronRight size={16} />
        </motion.span>
        <span className="flex-1">{title}</span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
