# Pain Radar — Architecture

## System Overview

Two-process monorepo: TypeScript frontend + Python research engine.

```
web/ (Next.js 15)  ←→  engine/ (Python FastAPI)
      ↓                       ↓
  Browser UI            Source Packs → LLM Analysis → Evidence Gate → Report
                              ↓
                          SQLite (data/)
```

## Key Design Decisions

### Evidence Gate (non-negotiable)
Every LLM output passes through `evidence_gate.py`. It rejects:
- Claims without `citation_indices`
- Citation indices that don't exist in the evidence pack
- Numeric values not found in cited excerpts
- Excerpts not found in stored source snapshots

Failed outputs retry up to 2x, then degrade to "insufficient evidence".

### Deterministic Query Templates
Search queries use keyword-slotted templates, not pure LLM generation.
LLM only extracts keywords (constrained to 3-5) and optionally adds 1-2 niche refinements.

### Source Snapshots
Every URL fetched is stored as raw text. Citations must be extractable from snapshots.
SERP snippets are used for discovery only — never as evidence.

### Recency Weighting
Evidence >24 months is downweighted (0.3) unless the niche is slow-moving (0.7).
Unknown dates get neutral weight (0.5).

### Conflict Detection
Contradictions between clusters or competitor claims are surfaced explicitly,
not smoothed over. Conflicts appear in the verdict.

## Pipeline Stages

1. INTAKE → parse idea, generate clarification questions
2. QUERY GENERATION → keywords + templates + niche refinement
3. EVIDENCE COLLECTION → Reddit, web search, reviews, hiring (parallel)
4. ANALYSIS → clustering, scoring, competitor extraction, payability (each gated)
5. CONFLICT DETECTION → find contradictions
6. VERDICT → KILL / NARROW / ADVANCE (gated)
7. VALIDATION PLAN → mandatory for all verdicts, adapts to verdict type
8. SKEPTIC PASS → red team review
9. ASSEMBLY → store in SQLite

## Running Locally

```bash
# Engine
cd engine && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp ../.env.example ../.env  # fill in API keys
.venv/bin/uvicorn pain_radar.main:app --reload --port 8000

# Web (separate terminal)
cd web && npm install
npm run dev
```

Open http://localhost:3000
