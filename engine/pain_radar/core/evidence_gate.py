"""Evidence Gate — validates that all LLM outputs reference real evidence.

Every analysis stage passes through this gate before its output is accepted.
If validation fails, the caller retries with the rejection reason appended to
the LLM prompt. After 3 failures, the field is marked "insufficient evidence".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from pydantic import BaseModel

from pain_radar.core.models import Citation, EvidencedClaim, SourceSnapshot

_NUM_PATTERN = re.compile(r"\b(\d+(?:[,.]\d+)?%?)\b")

# Stopwords for content-token extraction (excerpt validation)
_EXCERPT_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "what", "which", "who", "whom",
    "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most",
    "other", "some", "such", "no", "only", "same", "than", "too", "very",
    "just", "also", "now", "then", "here", "there", "when", "where", "how",
    "about", "above", "after", "again", "against", "below", "between",
    "from", "into", "through", "during", "before", "with", "without",
    "for", "of", "on", "in", "to", "at", "by", "up", "out", "off", "over",
})

MAX_RETRIES = 2  # retry up to 2 times (3 total attempts)


@dataclass
class GateViolation:
    field_path: str
    reason: str


@dataclass
class GateResult:
    passed: bool
    violations: list[GateViolation] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return "All evidence gates passed."
        lines = [f"Evidence gate failed with {len(self.violations)} violation(s):"]
        for v in self.violations:
            lines.append(f"  - [{v.field_path}]: {v.reason}")
        return "\n".join(lines)


def validate_output(
    output: BaseModel,
    evidence_pack: list[Citation],
    snapshots: dict[str, SourceSnapshot] | None = None,
) -> GateResult:
    """Validate that an LLM output meets all evidence requirements.

    1. Walk all EvidencedClaim fields in the output.
    2. Verify citation_indices are valid (exist in evidence_pack).
    3. If snapshots provided, verify excerpts exist in corresponding snapshots.
    4. Reject any freeform numeric in justification text that doesn't appear
       in a cited excerpt.
    """
    violations: list[GateViolation] = []
    # If the root object is itself an EvidencedClaim, validate it directly
    if isinstance(output, EvidencedClaim):
        _validate_claim(output, "<root>", evidence_pack, snapshots, violations)
    else:
        _walk_model(output, "", evidence_pack, snapshots, violations)
    return GateResult(passed=len(violations) == 0, violations=violations)


def _walk_model(
    obj: BaseModel,
    path: str,
    evidence_pack: list[Citation],
    snapshots: dict[str, SourceSnapshot] | None,
    violations: list[GateViolation],
) -> None:
    """Recursively walk a Pydantic model looking for EvidencedClaim fields."""
    for field_name, field_info in type(obj).model_fields.items():
        value = getattr(obj, field_name, None)
        if value is None:
            continue
        current_path = f"{path}.{field_name}" if path else field_name
        if isinstance(value, EvidencedClaim):
            _validate_claim(value, current_path, evidence_pack, snapshots, violations)
        elif isinstance(value, BaseModel):
            _walk_model(value, current_path, evidence_pack, snapshots, violations)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                item_path = f"{current_path}[{i}]"
                if isinstance(item, EvidencedClaim):
                    _validate_claim(item, item_path, evidence_pack, snapshots, violations)
                elif isinstance(item, BaseModel):
                    _walk_model(item, item_path, evidence_pack, snapshots, violations)


def _validate_claim(
    claim: EvidencedClaim,
    path: str,
    evidence_pack: list[Citation],
    snapshots: dict[str, SourceSnapshot] | None,
    violations: list[GateViolation],
) -> None:
    """Validate a single EvidencedClaim."""
    pack_size = len(evidence_pack)

    # 1. Check citation indices are valid
    for idx in claim.citation_indices:
        if idx < 0 or idx >= pack_size:
            violations.append(GateViolation(
                field_path=path,
                reason=f"Citation index {idx} out of range (pack size: {pack_size})",
            ))

    # 2. Check excerpts exist in snapshots (if snapshots provided)
    if snapshots:
        for idx in claim.citation_indices:
            if idx < 0 or idx >= pack_size:
                continue
            citation = evidence_pack[idx]
            snapshot = snapshots.get(citation.snapshot_hash)
            if snapshot and citation.excerpt not in snapshot.raw_text:
                violations.append(GateViolation(
                    field_path=path,
                    reason=(
                        f"Excerpt not found in snapshot for citation {idx}. "
                        f"Excerpt: '{citation.excerpt[:80]}...'"
                    ),
                ))

    # 3. Check freeform numerics are backed by cited excerpts
    numbers_in_text = _NUM_PATTERN.findall(claim.text)
    if numbers_in_text:
        # Collect all text from cited excerpts
        cited_excerpts = ""
        for idx in claim.citation_indices:
            if 0 <= idx < pack_size:
                cited_excerpts += " " + evidence_pack[idx].excerpt

        for num in numbers_in_text:
            # Skip trivially small numbers (0-5) which may be scores
            try:
                num_val = float(num.replace("%", "").replace(",", ""))
                if num_val <= 5:
                    continue
            except ValueError:
                pass
            if num not in cited_excerpts:
                violations.append(GateViolation(
                    field_path=path,
                    reason=(
                        f"Numeric value '{num}' in claim text not found in "
                        f"any cited excerpt. Numbers must come from evidence."
                    ),
                ))


# ---------------------------------------------------------------------------
# Excerpt validation + keyword-dense span selection
# ---------------------------------------------------------------------------

def _extract_content_tokens(text: str) -> list[str]:
    """Extract content tokens: lowercase words len>=5 and not stopwords."""
    words = re.sub(r"[^\w\s]", "", text.lower()).split()
    return [w for w in words if len(w) >= 5 and w not in _EXCERPT_STOPWORDS]


def _best_keyword_span(
    source_text: str,
    claim_text: str,
    span_len: int = 80,
) -> str:
    """Find the most keyword-dense span of ~span_len chars in source_text.

    Uses a sliding window scored by overlap of content tokens with claim_text.
    Prefers sentence boundaries when available.
    """
    if len(source_text) <= span_len:
        return source_text.strip()

    claim_tokens = set(_extract_content_tokens(claim_text))
    if not claim_tokens:
        # No meaningful claim tokens — return first span
        return source_text[:span_len].strip()

    # Try sentence-level first
    sentences = re.split(r"(?<=[.!?])\s+|\n+", source_text)
    if len(sentences) > 1:
        best_sent = ""
        best_score = -1
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 15:
                continue
            sent_tokens = set(_extract_content_tokens(sent))
            score = len(claim_tokens & sent_tokens)
            if score > best_score:
                best_score = score
                best_sent = sent
        if best_sent:
            return best_sent[:span_len].strip()

    # Sliding window fallback
    best_start = 0
    best_score = -1
    step = max(1, span_len // 4)
    for start in range(0, len(source_text) - span_len + 1, step):
        window = source_text[start:start + span_len]
        window_tokens = set(_extract_content_tokens(window))
        score = len(claim_tokens & window_tokens)
        if score > best_score:
            best_score = score
            best_start = start

    return source_text[best_start:best_start + span_len].strip()


def validate_and_fix_excerpts(
    claim: EvidencedClaim,
    evidence_pack: list[Citation],
) -> list[str]:
    """Validate evidence_excerpts against cited evidence. Fix invalid ones.

    For each excerpt:
    - Short excerpts (<8 content tokens): auto-replace with best span
    - Longer excerpts: require >=60% content-token overlap with cited evidence
    - On failure: auto-replace with keyword-dense span (never reject)

    Returns the (possibly fixed) list of excerpts.
    """
    if not claim.evidence_excerpts:
        return []

    pack_size = len(evidence_pack)
    valid_indices = [i for i in claim.citation_indices if 0 <= i < pack_size]
    if not valid_indices:
        return []

    cited_texts = [evidence_pack[i].excerpt for i in valid_indices]
    cited_tokens_by_source = [set(_extract_content_tokens(t)) for t in cited_texts]
    all_cited_tokens = set()
    for ts in cited_tokens_by_source:
        all_cited_tokens |= ts

    fixed = []
    for excerpt in claim.evidence_excerpts:
        excerpt_tokens = _extract_content_tokens(excerpt)

        # Short excerpt: skip overlap scoring, auto-replace
        if len(excerpt_tokens) < 8:
            best = _best_keyword_span(cited_texts[0], claim.text)
            fixed.append(best)
            continue

        # Check content-token overlap
        excerpt_token_set = set(excerpt_tokens)
        overlap = len(excerpt_token_set & all_cited_tokens)
        ratio = overlap / len(excerpt_token_set) if excerpt_token_set else 0

        if ratio >= 0.60:
            fixed.append(excerpt)
        else:
            # Auto-replace with best span from cited evidence
            best = _best_keyword_span(cited_texts[0], claim.text)
            fixed.append(best)

    return fixed


def auto_populate_excerpts(
    claim: EvidencedClaim,
    evidence_pack: list[Citation],
) -> list[str]:
    """Generate evidence excerpts from cited evidence when LLM omits them.

    Selects the best keyword-dense 80-char span from each of up to 2 distinct
    cited excerpts.
    """
    pack_size = len(evidence_pack)
    valid_indices = [i for i in claim.citation_indices if 0 <= i < pack_size]
    if not valid_indices:
        return []

    excerpts = []
    seen_urls: set[str] = set()
    for idx in valid_indices:
        citation = evidence_pack[idx]
        if citation.url in seen_urls:
            continue
        seen_urls.add(citation.url)
        span = _best_keyword_span(citation.excerpt, claim.text, span_len=80)
        if span:
            excerpts.append(span)
        if len(excerpts) >= 2:
            break

    return excerpts


# ---------------------------------------------------------------------------
# Fix 1: Absence claim auto-rewrite (render-time, clause-level only)
# ---------------------------------------------------------------------------

# Patterns that indicate unverifiable negative assertions
_ABSENCE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bno\s+(evidence|mention|response|discussion|data|signal)s?\b", re.I),
     "not observed in retrieved excerpts"),
    (re.compile(r"\bcontains?\s+no\b", re.I),
     "does not contain, in retrieved excerpts,"),
    (re.compile(r"\bzero\s+(mention|evidence|signal)s?\b", re.I),
     "no observed mentions in retrieved excerpts"),
    (re.compile(r"\babsence\s+of\b", re.I),
     "no observed presence in retrieved excerpts of"),
    (re.compile(r"\bno\s+.{3,30}\s+found\b", re.I),
     "not found in retrieved excerpts"),
]

# Whitelist — already hedged phrasing, skip rewrite
_ABSENCE_WHITELIST_PHRASES = [
    "not observed in",
    "not present in retrieved",
    "in retrieved excerpts",
]


def compute_display_rewrites(text: str) -> list[dict]:
    """Compute render-time absence rewrites for a claim text.

    Returns a list of rewrite dicts. Each has:
    - original: the matched phrase
    - rewritten: the replacement phrase
    - rule: "absence_rewrite"

    The raw text is NEVER mutated — these are display overrides only.
    """
    lower = text.lower()

    # Skip if already uses hedged phrasing
    if any(phrase in lower for phrase in _ABSENCE_WHITELIST_PHRASES):
        return []

    # Apply only the first matching pattern to avoid overlapping rewrites
    for pattern, replacement in _ABSENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            return [{
                "original": match.group(0),
                "rewritten": replacement,
                "rule": "absence_rewrite",
            }]

    return []


def apply_display_rewrites(text: str, rewrites: list[dict]) -> str:
    """Apply computed display rewrites to produce a display-only version.

    The original text should be stored unchanged. This produces the rendered version.
    """
    result = text
    for rw in rewrites:
        result = result.replace(rw["original"], rw["rewritten"], 1)
    return result


# ---------------------------------------------------------------------------
# Fix 2: Frequency adverb auto-downgrade (render-time, monotonic ladder)
# ---------------------------------------------------------------------------

_FREQUENCY_WORDS = re.compile(
    r"\b(frequently|often|common(?:ly)?|widespread|numerous|many\s+(?:users|people)"
    r"|routinely|regularly|pervasive(?:ly)?)\b",
    re.I,
)


def compute_frequency_downgrades(
    claim: EvidencedClaim,
    evidence_pack: list[Citation],
) -> list[dict]:
    """Compute render-time frequency word downgrades based on unique URL count.

    Monotonic ladder (never upgrades, never sidegrades):
    - n=1 unique URL: "in this source"
    - n=2: "in a couple of sources"
    - n=3-4: "in several sources"
    - n>=5: keep original word (earned)

    Returns a list of downgrade dicts. Each has:
    - original_word: the matched frequency word
    - replacement: the ladder phrase
    - unique_urls: how many unique URLs support this claim
    - rule: "frequency_downgrade"

    The raw text is NEVER mutated — these are display overrides only.
    """
    match = _FREQUENCY_WORDS.search(claim.text)
    if not match:
        return []

    # Count unique URLs among citation_indices
    pack_size = len(evidence_pack)
    valid_indices = [i for i in claim.citation_indices if 0 <= i < pack_size]
    unique_urls = len({evidence_pack[i].url for i in valid_indices})

    # Monotonic ladder
    if unique_urls >= 5:
        return []  # earned — keep original
    elif unique_urls >= 3:
        replacement = "in several sources"
    elif unique_urls == 2:
        replacement = "in a couple of sources"
    else:
        replacement = "in this source"

    return [{
        "original_word": match.group(0),
        "replacement": replacement,
        "unique_urls": unique_urls,
        "rule": "frequency_downgrade",
    }]


def apply_frequency_downgrades(text: str, downgrades: list[dict]) -> str:
    """Apply frequency downgrades to produce a display-only version."""
    result = text
    for dg in downgrades:
        result = result.replace(dg["original_word"], dg["replacement"], 1)
    return result
