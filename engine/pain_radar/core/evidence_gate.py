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
