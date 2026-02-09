"use client";

import { useState } from "react";
import { ExternalLink, Check, X as XIcon } from "lucide-react";
import type { Citation, Competitor } from "@/lib/types";
import { ClaimList } from "@/components/ui/claim-list";

const RELATIONSHIP_COLORS = {
  direct: "bg-red-400/10 text-red-400 border border-red-400/20",
  substitute: "bg-amber-400/10 text-amber-400 border border-amber-400/20",
  adjacent: "bg-zinc-700/50 text-zinc-500 border border-zinc-600/30",
} as const;

const RELATIONSHIP_BORDER_TOP = {
  direct: "border-t-2 border-t-red-400/40",
  substitute: "border-t-2 border-t-amber-400/40",
  adjacent: "border-t-2 border-t-zinc-600/40",
} as const;

interface CompetitorCardProps {
  competitor: Competitor;
  citations: Citation[];
}

export function CompetitorCard({ competitor, citations }: CompetitorCardProps) {
  const [expanded, setExpanded] = useState(false);
  const topBorder = competitor.relationship
    ? RELATIONSHIP_BORDER_TOP[competitor.relationship]
    : "";

  return (
    <div className={`neu-card p-4 ${topBorder}`}>
      <div className="flex items-start justify-between mb-2">
        <a
          href={competitor.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-zinc-200 hover:text-indigo-400 inline-flex items-center gap-1 transition-colors"
        >
          {competitor.name}
          <ExternalLink size={12} />
        </a>
        <span
          className={`inline-flex items-center gap-1 text-[10px] font-medium ${competitor.pricing_page_exists ? "text-green-400" : "text-zinc-600"}`}
        >
          {competitor.pricing_page_exists ? (
            <>
              <Check size={10} /> Pricing
            </>
          ) : (
            <>
              <XIcon size={10} /> No pricing
            </>
          )}
        </span>
      </div>
      <p className="text-xs text-zinc-500 mb-2 line-clamp-2">
        {competitor.positioning}
      </p>
      <div className="flex items-center gap-2 text-xs flex-wrap">
        {competitor.relationship && (
          <span
            className={`rounded-full px-2 py-0.5 font-medium ${RELATIONSHIP_COLORS[competitor.relationship]}`}
          >
            {competitor.relationship}
          </span>
        )}
        {competitor.min_price_observed && (
          <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-zinc-400">
            {competitor.min_price_observed}
          </span>
        )}
        <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-zinc-500 capitalize">
          {competitor.onboarding_model.replace("_", " ")}
        </span>
      </div>

      {(competitor.strengths.length > 0 ||
        competitor.weaknesses.length > 0) && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] text-zinc-600 hover:text-zinc-400 mt-2 transition-colors"
        >
          {expanded ? "Hide details" : "Show strengths & weaknesses"}
        </button>
      )}

      {expanded && (
        <div className="mt-2 space-y-2 text-xs">
          {competitor.strengths.length > 0 && (
            <div>
              <span className="text-green-400/80 font-medium">Strengths:</span>
              <ClaimList claims={competitor.strengths} citations={citations} />
            </div>
          )}
          {competitor.weaknesses.length > 0 && (
            <div>
              <span className="text-red-400/80 font-medium">Weaknesses:</span>
              <ClaimList claims={competitor.weaknesses} citations={citations} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
