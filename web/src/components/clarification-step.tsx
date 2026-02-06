"use client";

import { useState } from "react";
import { submitClarification } from "@/lib/api-client";
import type { ClarificationQuestion } from "@/lib/types";

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
    <form onSubmit={handleSubmit} className="w-full max-w-2xl space-y-6">
      <h2 className="text-lg font-medium text-zinc-200">
        A few questions before we dig in
      </h2>

      {questions.map((q) => (
        <div key={q.question} className="space-y-2">
          <label className="block text-sm text-zinc-300">{q.question}</label>
          {q.options ? (
            <div className="flex flex-wrap gap-2">
              {q.options.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setAnswer(q.question, opt)}
                  className={`rounded-full px-4 py-1.5 text-sm border transition-colors ${
                    answers[q.question] === opt
                      ? "bg-zinc-100 text-zinc-900 border-zinc-100"
                      : "border-zinc-700 text-zinc-400 hover:border-zinc-500"
                  }`}
                >
                  {opt}
                </button>
              ))}
              <input
                type="text"
                placeholder="Other..."
                onChange={(e) => {
                  if (e.target.value) setAnswer(q.question, e.target.value);
                }}
                className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-1.5 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
              />
            </div>
          ) : (
            <input
              type="text"
              value={answers[q.question] || ""}
              onChange={(e) => setAnswer(q.question, e.target.value)}
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
            />
          )}
        </div>
      ))}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg bg-zinc-100 px-6 py-2.5 font-medium text-zinc-900 hover:bg-zinc-200 disabled:opacity-50 transition-colors"
      >
        {submitting ? "Submitting..." : "Continue"}
      </button>
    </form>
  );
}
