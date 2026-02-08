"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Tag, Globe, Users, Lock, Loader2 } from "lucide-react";
import { startResearch } from "@/lib/api-client";
import { GlassCard } from "@/components/ui/glass-card";

const INPUT_CLASS =
  "w-full rounded-xl border border-zinc-700/60 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 transition-all duration-200 focus:border-indigo-400/60 focus:outline-none focus:ring-1 focus:ring-indigo-400/30 focus:shadow-[0_0_0_3px_rgba(129,140,248,0.08)]";

const FIELD_VARIANTS = {
  hidden: { opacity: 0, y: -8, height: 0 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    height: "auto" as const,
    transition: { delay: i * 0.05, duration: 0.25, ease: "easeOut" as const },
  }),
  exit: { opacity: 0, y: -8, height: 0, transition: { duration: 0.15 } },
};

const OPTIONAL_FIELDS = [
  { id: "niche", label: "Niche", icon: Tag, placeholder: "e.g., B2B SaaS, healthcare, fintech" },
  { id: "geography", label: "Geography", icon: Globe, placeholder: "e.g., US, Europe, Global" },
  { id: "buyer", label: "Who pays?", icon: Users, placeholder: "e.g., VP Engineering, Compliance Officer" },
  { id: "constraints", label: "Constraints", icon: Lock, placeholder: "e.g., No enterprise, budget under $5k" },
] as const;

export function IdeaForm() {
  const router = useRouter();
  const [idea, setIdea] = useState("");
  const [optionals, setOptionals] = useState<Record<string, string>>({
    niche: "",
    geography: "",
    buyer: "",
    constraints: "",
  });
  const [showOptional, setShowOptional] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateOptional(key: string, val: string) {
    setOptionals((prev) => ({ ...prev, [key]: val }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!idea.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await startResearch({
        idea: idea.trim(),
        niche: optionals.niche || undefined,
        geography: optionals.geography || undefined,
        buyer_role: optionals.buyer || undefined,
        constraints: optionals.constraints || undefined,
      });
      router.push(`/research/${res.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start research");
      setLoading(false);
    }
  }

  return (
    <GlassCard className="w-full max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Main textarea */}
        <div>
          <label
            htmlFor="idea"
            className="block text-sm font-medium text-zinc-300 mb-1.5"
          >
            Describe your business idea
          </label>
          <textarea
            id="idea"
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
            placeholder="e.g., A tool that automatically generates SOC 2 compliance reports for SaaS startups by connecting to their cloud infrastructure..."
            rows={5}
            className="w-full rounded-xl border border-zinc-700/60 bg-zinc-900/60 px-4 py-3 text-zinc-100 placeholder-zinc-600 transition-all duration-200 focus:border-indigo-400/60 focus:outline-none focus:ring-1 focus:ring-indigo-400/30 focus:shadow-[0_0_0_3px_rgba(129,140,248,0.08)] resize-y"
            required
          />
          <AnimatePresence>
            {idea.length > 0 && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mt-1 text-right text-xs text-zinc-600"
              >
                {idea.length} chars
                {idea.length > 100 && (
                  <span className="text-zinc-500">
                    {" "}
                    &mdash; detailed ideas get better results
                  </span>
                )}
              </motion.p>
            )}
          </AnimatePresence>
        </div>

        {/* Optional fields toggle */}
        <button
          type="button"
          onClick={() => setShowOptional(!showOptional)}
          className="flex items-center gap-1.5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <motion.span
            animate={{ rotate: showOptional ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="inline-flex"
          >
            <ChevronDown size={14} />
          </motion.span>
          Refine your search
        </button>

        {/* Optional fields */}
        <AnimatePresence>
          {showOptional && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className="overflow-hidden"
            >
              <div className="space-y-3 rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-4">
                {OPTIONAL_FIELDS.map((field, i) => (
                  <motion.div
                    key={field.id}
                    variants={FIELD_VARIANTS}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    custom={i}
                  >
                    <label
                      htmlFor={field.id}
                      className="flex items-center gap-1.5 text-sm text-zinc-400 mb-1"
                    >
                      <field.icon size={13} className="text-zinc-500" />
                      {field.label}
                    </label>
                    <input
                      id={field.id}
                      value={optionals[field.id]}
                      onChange={(e) => updateOptional(field.id, e.target.value)}
                      placeholder={field.placeholder}
                      className={INPUT_CLASS}
                    />
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="text-red-400 text-sm bg-red-950/50 border border-red-800/60 rounded-xl px-4 py-2.5"
            >
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Submit */}
        <motion.button
          type="submit"
          disabled={loading || !idea.trim()}
          whileTap={{ scale: 0.98 }}
          className="w-full rounded-xl bg-zinc-100 px-6 py-3 font-medium text-zinc-900 transition-colors hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Analyzing...
            </span>
          ) : (
            "Analyze Idea"
          )}
        </motion.button>
      </form>
    </GlassCard>
  );
}
