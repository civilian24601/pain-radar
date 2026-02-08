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

## Future Work: Search Infrastructure

### Tavily as secondary search source
Tavily (tavily.com) is an AI-optimized search API designed for RAG pipelines.
Key benefits over Serper for our use case:
- **Built-in relevance scores (0-1)** per result — could feed directly into evidence gate
- **`include_raw_content: "markdown"`** — returns cleaned page content, potentially
  skipping the separate fetch/snapshot step for some sources
- **`include_domains` / `exclude_domains`** — cleaner domain filtering than `site:` operators
- **Time range filtering** — `day`, `week`, `month`, `year` as first-class params

Cost: ~$0.005-0.008/query (vs Serper's ~$0.001). At ~45 queries/run, ~$0.35/run.
Free tier: 1,000 credits/month. Max 20 results/query.

Recommended approach: keep Serper as primary, add Tavily as a secondary source
for searches where pre-ranked relevance and built-in content extraction add value.

### Exa for semantic search (later phase)
Exa (exa.ai) uses neural/semantic search with its own index. Finds content by
meaning rather than keywords — useful for surfacing pain expressed in vocabulary
different from our search templates. Best as a complement, not replacement.

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
