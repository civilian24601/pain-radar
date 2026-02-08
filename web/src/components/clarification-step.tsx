"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { submitClarification } from "@/lib/api-client";
import type { ClarificationQuestion } from "@/lib/types";
import { GlassCard } from "@/components/ui/glass-card";

interface Props {
  jobId: string;
  questions: ClarificationQuestion[];
  onComplete: () => void;
}

export function ClarificationStep({ jobId, questions, onComplete }: Props) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  function setAnswer(question: string, value: string) {
    setAnswers((prev) => ({ ...prev, [question]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);

    const formatted = questions.map((q) => ({
      question: q.question,
      answer: answers[q.question] || "",
    }));

    try {
      await submitClarification(jobId, formatted);
      onComplete();
    } catch {
      setSubmitting(false);
    }
  }

  return (
    <GlassCard className="w-full max-w-2xl">
      <form onSubmit={handleSubmit} className="space-y-6">
        <h2 className="text-lg font-medium text-zinc-200">
          A few questions before we dig in
        </h2>

        {questions.map((q, qi) => (
          <motion.div
            key={q.question}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: qi * 0.08, duration: 0.3 }}
            className="space-y-2"
          >
            <label className="block text-sm text-zinc-300">
              {q.question}
            </label>
            {q.options ? (
              <div className="flex flex-wrap gap-2">
                {q.options.map((opt) => (
                  <motion.button
                    key={opt}
                    type="button"
                    whileTap={{ scale: 0.96 }}
                    onClick={() => setAnswer(q.question, opt)}
                    className={`rounded-full px-4 py-1.5 text-sm border transition-all duration-200 ${
                      answers[q.question] === opt
                        ? "bg-indigo-400/15 text-indigo-400 border-indigo-400/40"
                        : "border-zinc-700/60 text-zinc-400 hover:border-zinc-500"
                    }`}
                  >
                    {opt}
                  </motion.button>
                ))}
                <input
                  type="text"
                  placeholder="Other..."
                  onChange={(e) => {
                    if (e.target.value) setAnswer(q.question, e.target.value);
                  }}
                  className="rounded-full border border-zinc-700/60 bg-zinc-900/60 px-4 py-1.5 text-sm text-zinc-100 placeholder-zinc-600 focus:border-indigo-400/60 focus:outline-none focus:ring-1 focus:ring-indigo-400/30"
                />
              </div>
            ) : (
              <input
                type="text"
                value={answers[q.question] || ""}
                onChange={(e) => setAnswer(q.question, e.target.value)}
                className="w-full rounded-xl border border-zinc-700/60 bg-zinc-900/60 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 transition-all duration-200 focus:border-indigo-400/60 focus:outline-none focus:ring-1 focus:ring-indigo-400/30"
              />
            )}
          </motion.div>
        ))}

        <motion.button
          type="submit"
          disabled={submitting}
          whileTap={{ scale: 0.98 }}
          className="rounded-xl bg-zinc-100 px-6 py-2.5 font-medium text-zinc-900 transition-colors hover:bg-indigo-50 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <span className="inline-flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Submitting...
            </span>
          ) : (
            "Continue"
          )}
        </motion.button>
      </form>
    </GlassCard>
  );
}
