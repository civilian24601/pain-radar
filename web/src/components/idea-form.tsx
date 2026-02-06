"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { startResearch } from "@/lib/api-client";

export function IdeaForm() {
  const router = useRouter();
  const [idea, setIdea] = useState("");
  const [niche, setNiche] = useState("");
  const [geography, setGeography] = useState("");
  const [buyerRole, setBuyerRole] = useState("");
  const [constraints, setConstraints] = useState("");
  const [showOptional, setShowOptional] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!idea.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await startResearch({
        idea: idea.trim(),
        niche: niche || undefined,
        geography: geography || undefined,
        buyer_role: buyerRole || undefined,
        constraints: constraints || undefined,
      });
      router.push(`/research/${res.job_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start research");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl space-y-4">
      <div>
        <label htmlFor="idea" className="block text-sm font-medium text-zinc-300 mb-1">
          Describe your business idea
        </label>
        <textarea
          id="idea"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="e.g., A tool that automatically generates SOC 2 compliance reports for SaaS startups by connecting to their cloud infrastructure..."
          rows={5}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 resize-y"
          required
        />
      </div>

      <button
        type="button"
        onClick={() => setShowOptional(!showOptional)}
        className="text-sm text-zinc-400 hover:text-zinc-200 underline"
      >
        {showOptional ? "Hide" : "Show"} optional fields
      </button>

      {showOptional && (
        <div className="space-y-3 border border-zinc-800 rounded-lg p-4">
          <div>
            <label htmlFor="niche" className="block text-sm text-zinc-400 mb-1">Niche</label>
            <input
              id="niche"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              placeholder="e.g., B2B SaaS, healthcare, fintech"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="geography" className="block text-sm text-zinc-400 mb-1">Geography</label>
            <input
              id="geography"
              value={geography}
              onChange={(e) => setGeography(e.target.value)}
              placeholder="e.g., US, Europe, Global"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="buyer" className="block text-sm text-zinc-400 mb-1">Who pays?</label>
            <input
              id="buyer"
              value={buyerRole}
              onChange={(e) => setBuyerRole(e.target.value)}
              placeholder="e.g., VP Engineering, Compliance Officer, Solo founder"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
            />
          </div>
          <div>
            <label htmlFor="constraints" className="block text-sm text-zinc-400 mb-1">Constraints</label>
            <input
              id="constraints"
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              placeholder="e.g., No enterprise, budget under $5k, solo dev"
              className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
            />
          </div>
        </div>
      )}

      {error && (
        <div className="text-red-400 text-sm bg-red-950/50 border border-red-800 rounded px-3 py-2">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !idea.trim()}
        className="w-full rounded-lg bg-zinc-100 px-6 py-3 font-medium text-zinc-900 hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? "Starting research..." : "Analyze Idea"}
      </button>
    </form>
  );
}
