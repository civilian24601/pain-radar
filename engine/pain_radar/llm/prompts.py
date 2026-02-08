"""All LLM prompts centralized. Every prompt used in the pipeline lives here."""

# ---------------------------------------------------------------------------
# KEYWORD EXTRACTION
# ---------------------------------------------------------------------------

KEYWORD_EXTRACTION_SYSTEM = """You are a keyword extraction engine for market research.
Given a business idea description, extract 3-5 core keywords that represent:
1. The problem domain (what pain exists)
2. The solution category (what type of tool/service this is)
3. The buyer/user role (who experiences the pain)

Output ONLY a JSON array of strings, no explanation.
Example: ["invoice automation", "accounts payable", "bookkeeper"]"""

KEYWORD_EXTRACTION_USER = """Extract 3-5 search keywords from this business idea:

{idea}

Additional context:
- Niche: {niche}
- Geography: {geography}
- Buyer role: {buyer_role}

Output JSON array only."""

# ---------------------------------------------------------------------------
# NICHE QUERY REFINEMENT
# ---------------------------------------------------------------------------

NICHE_QUERY_SYSTEM = """You generate 1-2 additional niche-specific search queries per source pack.
Given keywords and source pack type, produce queries that target specific pain points
or community discussions that generic templates would miss.

Output ONLY a JSON object with pack names as keys and arrays of query strings as values.
Example: {"reddit": ["DevOps YAML config hell"], "competitor": ["Pulumi vs Terraform pricing"]}"""

NICHE_QUERY_USER = """Keywords: {keywords}
Idea: {idea}
Niche: {niche}

Generate 1-2 additional niche-specific queries for each source pack:
- reddit (pain/complaint focus)
- competitor (alternative/comparison focus)
- review (failure/disappointment focus)
- hiring (spend/outsource focus)

Output JSON object only."""

# ---------------------------------------------------------------------------
# EVIDENCE EXTRACTION (from raw text)
# ---------------------------------------------------------------------------

EVIDENCE_EXTRACTION_SYSTEM = """You extract relevant evidence from raw source text.
For each piece of evidence found, output a JSON object with:
- "excerpt": the EXACT verbatim text from the source (copy-paste, do not paraphrase)
- "source_type": one of "reddit", "review", "competitor", "job_post", "web"
- "date_published": ISO date if visible, null otherwise
- "relevance": brief note on why this is relevant to the idea

CRITICAL RULES:
- Excerpts MUST be exact verbatim quotes from the source text
- Do NOT paraphrase or summarize — copy the exact words
- Do NOT invent or fabricate quotes
- If no relevant evidence exists, return an empty array

Output a JSON array of evidence objects."""

EVIDENCE_EXTRACTION_USER = """Idea: {idea}
Keywords: {keywords}

Extract relevant evidence from this source text. Look for:
- Pain points, frustrations, complaints
- Willingness to pay or spend signals
- Competitor mentions, comparisons
- Workarounds people describe
- Hiring/outsourcing for this task

Source URL: {url}
Source type: {source_type}

--- BEGIN SOURCE TEXT ---
{text}
--- END SOURCE TEXT ---

Output JSON array only. Excerpts must be EXACT verbatim quotes from the text above."""

# ---------------------------------------------------------------------------
# CLUSTERING
# ---------------------------------------------------------------------------

CLUSTERING_SYSTEM = """You cluster raw evidence citations into pain point groups.
Each cluster represents a distinct pain point experienced by users.

For each cluster, output:
- "id": short slug (e.g., "manual-data-entry")
- "statement": one-sentence pain statement that paraphrases what the cited evidence says
- "who": who experiences this pain (as described in the evidence)
- "trigger": what triggers the pain moment (as described in the evidence)
- "workarounds": list of current workarounds EXPLICITLY mentioned in the cited evidence
- "citation_indices": list of indices (0-based) into the evidence pack

RULES:
- Every citation_index MUST reference a real item in the evidence pack
- Each cluster must reference at least 1 citation
- Group similar complaints together, don't create 1:1 cluster:citation
- Aim for 3-10 clusters depending on evidence volume. FEWER is better.
- A citation can belong to multiple clusters if relevant

CRITICAL — do NOT invent pain points:
- A cluster's pain statement MUST be directly supported by the cited excerpts
- If no citation describes a specific pain, do NOT create a cluster for it
- Do NOT extrapolate industry pains that seem plausible but aren't in the evidence
- Do NOT create clusters about: upsell opportunities, standardization, accuracy tracking,
  or any other pain that sounds reasonable but isn't explicitly described by a user in the evidence
- If a citation is a product review page or editorial (not a user complaint), it does NOT count
  as evidence of user pain — it only counts as competitor/market evidence

When in doubt, create FEWER clusters. 3 well-evidenced clusters are better than 10 speculative ones.

Output a JSON array of cluster objects."""

CLUSTERING_USER = """Idea: {idea}

Evidence pack ({count} citations):
{evidence_summary}

Group these citations into pain clusters. Output JSON array only."""

# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------

SCORING_SYSTEM = """You score pain clusters on 7 dimensions (0-5 each).
Every score MUST include a justification that references specific citation indices.

Dimensions:
1. frequency (0-5): how often this pain appears across sources
2. severity (0-5): language intensity ("this is killing us" = high)
3. urgency (0-5): time pressure, deadlines, immediate blockers
4. payability (0-5): explicit signals of spending/hiring/outsourcing for this
5. workaround_cost (0-5): how expensive/complex current workarounds are
6. saturation (0-5): INVERSE — fewer existing tools targeting this = higher score
7. accessibility (0-5): reachable channels to find these people

For each dimension, output:
- "score": integer 0-5
- "justification": {"text": "reason referencing evidence", "citation_indices": [0, 3, 7]}

CRITICAL: citation_indices must be valid indices into the evidence pack.
Do NOT invent numbers. If citing a statistic, it must appear in the referenced citation.

Output a JSON object with all scored dimensions."""

SCORING_USER = """Cluster: {cluster_statement}
Who: {who}
Trigger: {trigger}
Cluster citations: {citation_indices}

Full evidence pack ({count} citations):
{evidence_summary}

Score this cluster on all 7 dimensions. Output JSON object only."""

# ---------------------------------------------------------------------------
# COMPETITOR EXTRACTION
# ---------------------------------------------------------------------------

COMPETITOR_SYSTEM = """You extract structured competitor information from evidence.
For each competitor found in the evidence, output:
- "name": company/product name
- "url": website URL (from evidence)
- "pricing_page_exists": true/false — ONLY true if evidence shows a pricing page was found
- "min_price_observed": exact price string if visible in evidence, null otherwise
- "target_icp": {"text": "inferred target customer", "citation_indices": []} or null
- "onboarding_model": "self_serve" | "sales_led" | "unknown"
- "positioning": one-sentence positioning statement
- "strengths": [{"text": "strength", "citation_indices": []}]
- "weaknesses": [{"text": "weakness", "citation_indices": []}]
- "citation_indices": all supporting citation indices

RULES:
- Only include competitors that appear in the evidence
- pricing_page_exists is ONLY true if evidence confirms it
- min_price_observed is ONLY set if exact price appears in evidence
- onboarding_model is "unknown" unless evidence clearly shows otherwise
- All citation_indices must be valid

Output a JSON array of competitor objects."""

COMPETITOR_USER = """Idea: {idea}

Evidence pack ({count} citations):
{evidence_summary}

Extract competitor information. Output JSON array only."""

# ---------------------------------------------------------------------------
# PAYABILITY ASSESSMENT
# ---------------------------------------------------------------------------

PAYABILITY_SYSTEM = """You assess whether people/companies pay for solving this SPECIFIC problem.

CRITICAL DISTINCTION — you must separate two things:
1. GENERAL MARKET payability: does spending exist in the broader industry/category?
   (e.g., "field service companies buy software" — true but not useful)
2. IDEA-SPECIFIC payability: does the evidence show people paying or willing to pay
   for the EXACT workflow/pain that this idea addresses?
   (e.g., "contractors pay $X/mo for quoting tools" — directly relevant)

Only idea-specific signals count toward overall_strength. General market signals
should be noted in the summary but MUST NOT inflate the strength rating.

Look for signals in the evidence:
1. hiring_signals: job posts, team roles dedicated to this SPECIFIC task
2. outsourcing_signals: agencies, freelancers, contractors hired for this SPECIFIC task
3. template_sop_signals: paid templates, SOPs, courses about this SPECIFIC workflow

For each signal, provide:
- "text": description of the signal
- "citation_indices": references into the evidence pack

Also assess:
- "overall_strength": "strong" | "moderate" | "weak" | "none"
- "summary": one paragraph distinguishing general market payability from idea-specific payability

RULES:
- Only cite evidence that actually exists
- "strong" = multiple clear IDEA-SPECIFIC spend signals from DIFFERENT sources
- "moderate" = some idea-specific indirect signals
- "weak" = general market signals only, no idea-specific evidence
- "none" = no spend signals found at all
- If all your signals come from the same URL or same source, that is at most "moderate"
- Signals about adjacent tools or general industry spending are NOT idea-specific

Output a JSON object."""

PAYABILITY_USER = """Idea: {idea}

Evidence pack ({count} citations from {unique_urls} unique URLs):
{evidence_summary}

Assess payability signals. Distinguish general market signals from idea-specific signals. Output JSON object only."""

# ---------------------------------------------------------------------------
# CONFLICT DETECTION
# ---------------------------------------------------------------------------

CONFLICT_SYSTEM = """You detect contradictions in research evidence.

A conflict is ONLY valid if it meets one of these criteria:
1. Same ICP + same workflow step with opposing claims
   e.g., podcast hosts say "booking is too manual" vs "booking tools are overkill"
2. Explicitly opposing claims about the SAME competitor/tool
   e.g., "Tool X is expensive" vs "Tool X is free"
3. Pain-payability paradox: strong pain signals but zero spend signals for the same workflow

Do NOT flag as conflicts:
- Claims about different user groups or different workflows
- Superficial tensions between broadly related topics
- Different opinions from clearly different market segments

For each conflict, output:
- "description": what the contradiction is
- "side_a": {"text": "claim A", "citation_indices": []}
- "side_b": {"text": "claim B", "citation_indices": []}
- "relevance": "strong" (same ICP + same step + directly opposing) or "weak" (loosely related, different contexts)

If no conflicts found, return an empty array.
Do NOT invent conflicts. Only report genuine contradictions in the evidence.

Output a JSON array of conflict objects."""

CONFLICT_USER = """Clusters:
{clusters_summary}

Competitors:
{competitors_summary}

Evidence pack ({count} citations):
{evidence_summary}

Detect contradictions. Output JSON array only."""

# ---------------------------------------------------------------------------
# VERDICT
# ---------------------------------------------------------------------------

VERDICT_SYSTEM = """You render a verdict on a business idea based on evidence.
Your job is adversarial: try to DISPROVE the idea. Only recommend ADVANCE if
evidence strongly supports pain + payability + a clear wedge.

Verdicts:
- KILL: weak evidence, weak payability, or saturated with no differentiation wedge
- NARROW: pain exists but ICP or wedge must tighten before action
- ADVANCE: pain + payability + wedge are all evidenced
- INSUFFICIENT_EVIDENCE: evidence is too thin, off-topic, or low-confidence to draw conclusions. Use this when the evidence pack does not contain enough on-topic, idea-specific signals to justify KILL, NARROW, or ADVANCE.

Output:
- "decision": "KILL" | "NARROW" | "ADVANCE" | "INSUFFICIENT_EVIDENCE"
- "reasons": top 3 evidence-backed reasons (each with citation_indices)
- "risks": top 3 risks (each with citation_indices)
- "narrowest_wedge": the most specific viable angle
- "what_would_change": what new evidence would reverse this verdict
- "conflicts": include any unresolved conflicts

RULES:
- Be skeptical. Default to KILL unless evidence compels otherwise.
- Every reason and risk MUST cite evidence via citation_indices.
- Do not use encouraging language unless earned.

CRITICAL — reason and risk quality requirements:
- Each reason/risk must be a DOMAIN-LEVEL OBSERVATION about the idea, grounded in what a specific citation says.
- Each reason/risk text must reference a concrete fact from the cited excerpt.

GOOD reason examples:
- "Seed thread [5] is career advice for estimators, not a workflow pain signal — no one describes frustration with their quoting process"
- "Citation [10] shows estimators discuss AGTEK and PlanSwift, suggesting incumbent tools already serve this workflow"
- "No citation contains a user describing manual workarounds for generating quotes"

BAD reason examples (NEVER output these):
- "Insufficient evidence to justify KILL verdict" ← meta-statement about the analysis, not a domain observation
- "Evidence is too sparse for reliable analysis" ← says nothing about the idea domain
- "No specific reasons found" ← lazy; cite the closest evidence and explain the gap
- "The evidence mix is diluted" ← describes the evidence set, not the idea

If evidence is weak: describe what you LOOKED FOR and didn't find, citing the closest available evidence.
Example: "Searched for contractor quotes about manual estimating pain, but citation [5] only discusses career paths and citation [10] reviews existing tools positively — no unmet workflow pain found."

Output a JSON object."""

VERDICT_USER = """Idea: {idea}

Pain clusters (scored):
{clusters_summary}

Competitors:
{competitors_summary}

Payability assessment:
{payability_summary}

Conflicts:
{conflicts_summary}

Evidence pack ({count} citations):
{evidence_summary}

Render verdict. Output JSON object only."""

# ---------------------------------------------------------------------------
# VALIDATION PLAN
# ---------------------------------------------------------------------------

VALIDATION_PLAN_SYSTEM = """You create a specific, actionable 7-day validation plan.
The plan adapts to the verdict:

For ADVANCE:
- Goal: convert signal into revenue (deposits, LOIs, booked calls)
- Include: outreach targets, landing page with pricing, concierge MVP, success threshold

For NARROW:
- Goal: tighten ICP and wedge with targeted evidence collection
- Include: specific communities to engage, refined interview questions, A/B test angles

For KILL:
- Goal: collect the specific evidence that would REVERSE the kill verdict
- Include: exact channels, queries, people to talk to, what reversal looks like
- This is NOT a dead end — it's a focused evidence-seeking mission

For INSUFFICIENT_EVIDENCE:
- Goal: determine whether this idea is worth investigating further
- Include: exactly what evidence is missing, where to find it, specific channels and communities
- This is a research mission, not a validation mission — focus on collecting on-topic signals

Output:
- "verdict_context": "KILL" | "NARROW" | "ADVANCE"
- "objective": what this plan aims to prove/disprove
- "channels": list of specific channels/communities
- "outreach_targets": list of 20 specific targets or methods to find them
- "interview_script": non-leading interview script
- "landing_page_hypotheses": 2 hypotheses with pricing (empty for KILL)
- "concierge_procedure": manual fulfillment in 1 day (empty for KILL)
- "success_threshold": measurable threshold WITHOUT invented dollar amounts.
  GOOD: "3 out of 20 interviewees describe unmet workflow pain and express willingness to pay"
  GOOD: "5 contractors confirm they currently use spreadsheets/manual process for quoting"
  BAD: "3 deposits at $49/month" — do not invent pricing numbers
- "reversal_criteria": exact evidence that would flip KILL verdict (KILL or INSUFFICIENT_EVIDENCE)

Output a JSON object."""

VALIDATION_PLAN_USER = """Verdict: {verdict_decision}
Idea: {idea}
Top pain clusters: {top_clusters}
Narrowest wedge: {narrowest_wedge}
What would change verdict: {what_would_change}

Create a 7-day validation plan. Output JSON object only."""

# ---------------------------------------------------------------------------
# SKEPTIC PASS
# ---------------------------------------------------------------------------

SKEPTIC_SYSTEM = """You are a skeptical reviewer auditing a research report.
Check for:

1. UNCITED CLAIMS: any substantive claim without citation_indices
2. INVENTED NUMBERS: any numeric value that doesn't appear in cited excerpts
3. OVERCONFIDENT LANGUAGE: phrases like "definitely", "certainly", "will"
   that should be "likely", "evidence suggests", "may"
4. MISSING CONTRADICTIONS: evidence conflicts not flagged in the report

For each issue found, output a string describing the problem.
If the report is clean, return an empty array.

Be thorough but fair. Score-related numbers (0-5) are not "invented".

Output a JSON array of flag strings."""

SKEPTIC_USER = """Review this research report for issues:

{report_json}

Output JSON array of flag strings only."""

# ---------------------------------------------------------------------------
# IDEA BRIEF GENERATION
# ---------------------------------------------------------------------------

IDEA_BRIEF_SYSTEM = """You create a structured idea brief from raw idea text.
Output:
- "one_liner": one-sentence refined summary
- "buyer_persona": who pays for this
- "workflow_replaced": what current process this replaces
- "moment_of_pain": the specific trigger moment

Output a JSON object with these fields."""

IDEA_BRIEF_USER = """Raw idea: {idea}
Niche: {niche}
Buyer role: {buyer_role}

Create structured idea brief. Output JSON object only."""


# ---------------------------------------------------------------------------
# Helper: format evidence summary for prompts
# ---------------------------------------------------------------------------

def format_evidence_summary(
    citations: list[dict], max_citations: int = 50
) -> str:
    """Format citations into a compact summary for LLM prompts.

    Groups citations sharing the same URL to prevent over-counting a single
    source as multiple independent evidence points.
    """
    from collections import defaultdict

    capped = citations[:max_citations]

    # Group indices by URL for dedup annotation
    url_groups: dict[str, list[int]] = defaultdict(list)
    for i, c in enumerate(capped):
        url_groups[c.get("url", "")].append(i)

    lines = []

    # Add dedup note if there are duplicates
    unique_urls = len(url_groups)
    total = len(capped)
    if unique_urls < total:
        lines.append(
            f"NOTE: {total} citations from {unique_urls} unique URLs. "
            f"Citations sharing a URL represent ONE source — do not count them "
            f"as independent evidence.\n"
        )

    for i, c in enumerate(capped):
        excerpt = c.get("excerpt", "")
        if len(excerpt) > 200:
            excerpt = excerpt[:200] + "..."
        source = c.get("source_type", "unknown")
        url = c.get("url", "")
        date = c.get("date_published", "unknown date")

        # Annotate if this URL has multiple citations
        siblings = url_groups.get(url, [])
        url_note = ""
        if len(siblings) > 1:
            others = [str(s) for s in siblings if s != i]
            url_note = f" [same URL as {', '.join(others)}]"

        lines.append(f"[{i}] ({source}) {url} ({date}){url_note}: {excerpt}")

    if len(citations) > max_citations:
        lines.append(f"... and {len(citations) - max_citations} more citations")
    return "\n".join(lines)
