"""Pain clustering — group raw evidence into pain clusters."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from pain_radar.core.evidence_gate import MAX_RETRIES, validate_output
from pain_radar.core.models import (
    Citation,
    ClusterCategory,
    ClusterScores,
    Competitor,
    CompetitorRelationship,
    EvidencedClaim,
    IdeaBrief,
    OnboardingModel,
    PainCluster,
    ScoredDimension,
    SourceType,
)
from pain_radar.llm.prompts import (
    CLUSTERING_SYSTEM,
    CLUSTERING_USER,
    COMPETITOR_SYSTEM,
    COMPETITOR_USER,
    format_evidence_summary,
)

if TYPE_CHECKING:
    from pain_radar.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def cluster_evidence(
    citations: list[Citation],
    idea: str,
    options: dict,
    llm: LLMProvider,
    idea_brief: IdeaBrief | None = None,
) -> list[PainCluster]:
    """Group citations into pain clusters via LLM. Output passes evidence gate."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)

    prompt_content = CLUSTERING_USER.format(
        idea=idea,
        count=len(citations),
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=CLUSTERING_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=8192,
            )

            if not isinstance(raw, list):
                raw = [raw]

            clusters = []
            for item in raw:
                cluster = _parse_cluster(item, len(citations))
                if cluster:
                    clusters.append(cluster)

            if not clusters:
                logger.warning(f"Clustering attempt {attempt + 1}: no valid clusters")
                prompt_content += "\n\nPrevious attempt produced no valid clusters. Try again with valid citation_indices."
                continue

            # Classify clusters as core vs context
            if idea_brief:
                for cluster in clusters:
                    cluster.category = _classify_cluster(
                        cluster.statement.text,
                        idea_brief.keywords,
                        idea_brief.workflow_verbs,
                        idea_brief.incumbent_tools,
                    )
            # Sort: CORE first, CONTEXT second
            clusters.sort(key=lambda c: 0 if c.category == ClusterCategory.CORE else 1)
            return clusters

        except Exception:
            logger.exception(f"Clustering attempt {attempt + 1} failed")
            if attempt < MAX_RETRIES:
                prompt_content += "\n\nPrevious attempt failed. Output valid JSON array of cluster objects."

    logger.error("Clustering exhausted all retries")
    return []


def _parse_cluster(item: dict, pack_size: int) -> PainCluster | None:
    """Parse a raw cluster dict into a PainCluster, validating indices."""
    try:
        citation_indices = item.get("citation_indices", [])
        # Filter to valid indices
        valid_indices = [i for i in citation_indices if 0 <= i < pack_size]
        if not valid_indices:
            return None

        # Build placeholder scores (will be filled by scoring stage)
        placeholder_dim = ScoredDimension(
            score=0,
            justification=EvidencedClaim(
                text="Pending scoring",
                citation_indices=valid_indices[:1],
            ),
        )
        placeholder_scores = ClusterScores(
            frequency=placeholder_dim,
            severity=placeholder_dim,
            urgency=placeholder_dim,
            payability=placeholder_dim,
            workaround_cost=placeholder_dim,
            saturation=placeholder_dim,
            accessibility=placeholder_dim,
        )

        # Read LLM-provided category as initial hint (deterministic override later)
        raw_category = item.get("category", "core").lower()
        try:
            category = ClusterCategory(raw_category)
        except ValueError:
            category = ClusterCategory.CORE

        return PainCluster(
            id=item.get("id", "unknown"),
            statement=EvidencedClaim(
                text=item.get("statement", "Unknown pain"),
                citation_indices=valid_indices[:3],
            ),
            who=item.get("who", "Unknown"),
            trigger=item.get("trigger", "Unknown"),
            workarounds=item.get("workarounds", []),
            citation_indices=valid_indices,
            scores=placeholder_scores,
            confidence=0.5,
            recency_weight=1.0,
            category=category,
        )
    except Exception:
        logger.exception("Failed to parse cluster")
        return None


# ---------------------------------------------------------------------------
# Gravity patterns — cross-domain pains that are real but not product wedges
# ---------------------------------------------------------------------------
_GRAVITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bmanual\s+(?:process|data\s+entry|work|task|input|step)",
        r"\bdata\s+entry\b",
        r"\black\s+of\s+integration\b",
        r"\bcommunication\s+(?:gap|issue|problem|breakdown)",
        r"\btime[\s-]consuming\b",
        r"\brepetitive\s+task",
        r"\binefficient\s+(?:process|workflow)",
        r"\bspreadsheet\s+(?:chaos|hell|mess|overload)",
        r"\bemail\s+(?:overload|chaos|back[\s-]and[\s-]forth)",
        r"\bsiloed?\s+(?:data|information|system)",
    ]
]

# Common stopwords excluded from keyword matching (len < 5 already excluded)
_CLASSIFY_STOPWORDS = frozenset({
    "about", "after", "again", "being", "between", "could", "doing",
    "during", "every", "from", "going", "great", "having", "issue",
    "issues", "needs", "often", "other", "their", "there", "these",
    "thing", "things", "those", "using", "users", "where", "which",
    "while", "would", "people", "really", "should", "still", "every",
    "through", "before",
})


def _normalize_tokens(text: str) -> set[str]:
    """Lowercase, split, keep words len >= 5, drop stopwords."""
    return {
        w for w in re.findall(r"[a-z]{5,}", text.lower())
        if w not in _CLASSIFY_STOPWORDS
    }


def _classify_cluster(
    statement: str,
    idea_keywords: list[str],
    workflow_verbs: list[str],
    incumbent_tools: list[str],
) -> ClusterCategory:
    """Deterministic core vs context classification.

    CORE requires: at least one workflow verb phrase match OR one incumbent
    tool mention in the cluster statement. If >=2 normalized idea keyword
    matches, confirm CORE regardless.

    CONTEXT if: matches a gravity pattern AND has zero idea keyword matches
    AND zero workflow verb matches.
    """
    stmt_lower = statement.lower()
    stmt_tokens = _normalize_tokens(statement)

    # --- Check workflow verb phrase matches ---
    has_workflow_match = False
    for verb in workflow_verbs:
        # Phrase-level match (e.g. "re-key into QuickBooks")
        if verb.lower() in stmt_lower:
            has_workflow_match = True
            break
        # Token-level fallback: require 2+ content tokens from the verb phrase
        verb_tokens = _normalize_tokens(verb)
        if verb_tokens and len(stmt_tokens & verb_tokens) >= min(2, len(verb_tokens)):
            has_workflow_match = True
            break

    # --- Check incumbent tool mentions ---
    has_tool_match = False
    for tool in incumbent_tools:
        if tool.lower() in stmt_lower:
            has_tool_match = True
            break

    # --- Count normalized idea keyword matches ---
    kw_tokens = set()
    for kw in idea_keywords:
        kw_tokens |= _normalize_tokens(kw)
    keyword_overlap = len(stmt_tokens & kw_tokens)

    # --- Classification rules ---
    # Rule 1: >=2 keyword matches → CORE regardless
    if keyword_overlap >= 2:
        return ClusterCategory.CORE

    # Rule 2: workflow verb or tool mention → CORE
    if has_workflow_match or has_tool_match:
        return ClusterCategory.CORE

    # Rule 3: gravity pattern + zero keyword/verb matches → CONTEXT
    matches_gravity = any(p.search(stmt_lower) for p in _GRAVITY_PATTERNS)
    if matches_gravity and keyword_overlap == 0 and not has_workflow_match:
        return ClusterCategory.CONTEXT

    # Rule 4: single keyword match (but no gravity) → CORE (benefit of the doubt)
    if keyword_overlap >= 1:
        return ClusterCategory.CORE

    # Default: CORE (conservative — don't hide clusters)
    return ClusterCategory.CORE


# ---------------------------------------------------------------------------
# Labor/service substitute patterns
# ---------------------------------------------------------------------------
_SUBSTITUTE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bagency\b",
        r"\bfreelancer",
        r"\boutsourc",
        r"\bvirtual\s+assistant",
        r"\b(?:VA|VAs)\b",
        r"\bbookkeeping\s+service",
        r"\bwe\s+do\s+it\s+for\s+you",
        r"\bmanaged\s+service",
        r"\bfull[\s-]service",
        r"\bdone[\s-]for[\s-]you",
    ]
]


def _classify_competitor_relationship(
    name: str,
    positioning: str,
    strengths_text: str,
    llm_label: str,
    idea_brief: IdeaBrief | None,
) -> CompetitorRelationship:
    """Deterministic-first competitor relationship classification with guardrails.

    Rules:
    1. Incumbent tool match + workflow verb overlap → DIRECT
    2. Labor/service substitute pattern → SUBSTITUTE
    3. Keyword overlap >= 3 but no workflow verb match → SUBSTITUTE
    4. Fallback: use LLM label, but override to ADJACENT if LLM says DIRECT
       and neither Rule 1 nor Rule 3 (>=3 overlap) is satisfied.
    """
    if not idea_brief:
        # No idea brief — trust LLM label but cap at SUBSTITUTE
        try:
            rel = CompetitorRelationship(llm_label.lower())
        except ValueError:
            rel = CompetitorRelationship.ADJACENT
        if rel == CompetitorRelationship.DIRECT:
            return CompetitorRelationship.ADJACENT
        return rel

    combined_text = f"{positioning} {strengths_text}".lower()
    name_lower = name.lower()

    # --- Check incumbent tool match ---
    is_incumbent = any(
        tool.lower() in name_lower or name_lower in tool.lower()
        for tool in idea_brief.incumbent_tools
    )

    # --- Check workflow verb overlap in positioning/strengths ---
    has_workflow_overlap = False
    for verb in idea_brief.workflow_verbs:
        if verb.lower() in combined_text:
            has_workflow_overlap = True
            break
        # Token-level fallback
        verb_tokens = _normalize_tokens(verb)
        combined_tokens = _normalize_tokens(combined_text)
        if verb_tokens and len(combined_tokens & verb_tokens) >= min(2, len(verb_tokens)):
            has_workflow_overlap = True
            break

    # Also check moment_of_pain overlap
    if not has_workflow_overlap and idea_brief.moment_of_pain:
        if idea_brief.moment_of_pain.lower() in combined_text:
            has_workflow_overlap = True
        else:
            # Token-level fallback for moment_of_pain
            mop_tokens = _normalize_tokens(idea_brief.moment_of_pain)
            combined_tokens = _normalize_tokens(combined_text)
            if mop_tokens and len(combined_tokens & mop_tokens) >= min(2, len(mop_tokens)):
                has_workflow_overlap = True

    # Rule 1: incumbent tool + workflow overlap → DIRECT
    if is_incumbent and has_workflow_overlap:
        return CompetitorRelationship.DIRECT

    # Rule 2: labor/service substitute
    if any(p.search(combined_text) for p in _SUBSTITUTE_PATTERNS):
        return CompetitorRelationship.SUBSTITUTE

    # Rule 3: keyword overlap >= 3 without workflow match → SUBSTITUTE
    kw_tokens = set()
    for kw in idea_brief.keywords:
        kw_tokens |= _normalize_tokens(kw)
    combined_tokens = _normalize_tokens(combined_text)
    keyword_overlap = len(combined_tokens & kw_tokens)

    if keyword_overlap >= 3 and not has_workflow_overlap:
        return CompetitorRelationship.SUBSTITUTE

    # Rule 4: LLM label as fallback with guardrail
    try:
        rel = CompetitorRelationship(llm_label.lower())
    except ValueError:
        rel = CompetitorRelationship.ADJACENT

    # Guardrail: LLM can't say DIRECT unless Rule 1 or Rule 3 (>=3 overlap) met
    if rel == CompetitorRelationship.DIRECT:
        if not (is_incumbent and has_workflow_overlap) and keyword_overlap < 3:
            return CompetitorRelationship.ADJACENT

    return rel


async def extract_competitors(
    citations: list[Citation],
    idea: str,
    options: dict,
    llm: LLMProvider,
    idea_brief: IdeaBrief | None = None,
) -> list[Competitor]:
    """Extract competitor information from evidence. Output passes evidence gate."""
    evidence_dicts = [c.model_dump() for c in citations]
    evidence_summary = format_evidence_summary(evidence_dicts)

    prompt_content = COMPETITOR_USER.format(
        idea=idea,
        count=len(citations),
        evidence_summary=evidence_summary,
    )

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = await llm.complete_json(
                system=COMPETITOR_SYSTEM,
                messages=[{"role": "user", "content": prompt_content}],
                max_tokens=8192,
            )

            if not isinstance(raw, list):
                raw = [raw]

            competitors = []
            for item in raw:
                comp = _parse_competitor(item, len(citations))
                if comp:
                    # Classify relationship deterministically
                    strengths_text = " ".join(s.text for s in comp.strengths)
                    llm_label = item.get("relationship", "adjacent")
                    comp.relationship = _classify_competitor_relationship(
                        comp.name,
                        comp.positioning,
                        strengths_text,
                        llm_label,
                        idea_brief,
                    )
                    competitors.append(comp)

            return competitors

        except Exception:
            logger.exception(f"Competitor extraction attempt {attempt + 1} failed")

    return []


def _parse_competitor(item: dict, pack_size: int) -> Competitor | None:
    """Parse a raw competitor dict into a Competitor model."""
    try:
        citation_indices = [i for i in item.get("citation_indices", []) if 0 <= i < pack_size]
        if not citation_indices:
            return None

        # Parse strengths/weaknesses as EvidencedClaims
        strengths = []
        for s in item.get("strengths", []):
            if isinstance(s, dict) and s.get("text"):
                indices = [i for i in s.get("citation_indices", []) if 0 <= i < pack_size]
                if indices:
                    strengths.append(EvidencedClaim(text=s["text"], citation_indices=indices))

        weaknesses = []
        for w in item.get("weaknesses", []):
            if isinstance(w, dict) and w.get("text"):
                indices = [i for i in w.get("citation_indices", []) if 0 <= i < pack_size]
                if indices:
                    weaknesses.append(EvidencedClaim(text=w["text"], citation_indices=indices))

        # Ensure at least one strength/weakness placeholder
        if not strengths:
            strengths = [EvidencedClaim(text="No strengths identified in evidence", citation_indices=citation_indices[:1])]
        if not weaknesses:
            weaknesses = [EvidencedClaim(text="No weaknesses identified in evidence", citation_indices=citation_indices[:1])]

        # Parse target_icp
        target_icp = None
        if item.get("target_icp") and isinstance(item["target_icp"], dict):
            icp_indices = [i for i in item["target_icp"].get("citation_indices", []) if 0 <= i < pack_size]
            if icp_indices:
                target_icp = EvidencedClaim(
                    text=item["target_icp"].get("text", ""),
                    citation_indices=icp_indices,
                )

        # Parse onboarding model
        onboarding_raw = item.get("onboarding_model", "unknown")
        try:
            onboarding = OnboardingModel(onboarding_raw)
        except ValueError:
            onboarding = OnboardingModel.UNKNOWN

        return Competitor(
            name=item.get("name", "Unknown"),
            url=item.get("url", ""),
            pricing_page_exists=bool(item.get("pricing_page_exists", False)),
            min_price_observed=item.get("min_price_observed"),
            target_icp=target_icp,
            onboarding_model=onboarding,
            positioning=item.get("positioning", ""),
            strengths=strengths,
            weaknesses=weaknesses,
            citation_indices=citation_indices,
        )
    except Exception:
        logger.exception("Failed to parse competitor")
        return None
