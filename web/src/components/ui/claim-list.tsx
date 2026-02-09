"use client";

import type { Citation, EvidencedClaim } from "@/lib/types";
import { CitationChip } from "@/components/ui/citation-chip";

interface ClaimListProps {
  claims: EvidencedClaim[];
  citations: Citation[];
}

export function ClaimList({ claims, citations }: ClaimListProps) {
  return (
    <ul className="space-y-3">
      {claims.map((claim, i) => (
        <li key={i}>
          <p className="text-sm text-zinc-300 leading-relaxed">
            {claim.text}
            <span className="ml-1.5 inline-flex gap-1">
              {claim.citation_indices.map((idx) => (
                <CitationChip
                  key={idx}
                  index={idx}
                  url={citations[idx]?.url || "#"}
                  excerpt={citations[idx]?.excerpt}
                />
              ))}
            </span>
          </p>
          {claim.evidence_excerpts && claim.evidence_excerpts.length > 0 && (
            <div className="mt-1.5 ml-3 space-y-1">
              {claim.evidence_excerpts.map((excerpt, ei) => (
                <p
                  key={ei}
                  className="neu-inset rounded-lg px-3 py-1.5 text-xs italic text-zinc-400 leading-relaxed"
                >
                  &ldquo;{excerpt}&rdquo;
                </p>
              ))}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
