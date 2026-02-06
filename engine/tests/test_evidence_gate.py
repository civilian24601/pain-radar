"""Tests for the evidence gate validation system."""

import pytest
from pydantic import ValidationError

from pain_radar.core.evidence_gate import validate_output, GateResult
from pain_radar.core.models import (
    Citation,
    ClusterScores,
    EvidencedClaim,
    PainCluster,
    ScoredDimension,
    SourceSnapshot,
    SourceType,
)


def _make_citation(index: int, excerpt: str = "test excerpt") -> Citation:
    return Citation(
        url=f"https://example.com/{index}",
        excerpt=excerpt,
        source_type=SourceType.REDDIT,
        date_published=None,
        date_retrieved="2025-01-01T00:00:00Z",
        recency_months=None,
        snapshot_hash=f"hash{index}",
    )


def _make_snapshot(hash: str, raw_text: str) -> SourceSnapshot:
    return SourceSnapshot(
        url=f"https://example.com/{hash}",
        content_hash=hash,
        raw_text=raw_text,
        fetched_at="2025-01-01T00:00:00Z",
        storage_path=f"/tmp/{hash}.txt",
    )


class TestEvidencedClaim:
    def test_rejects_empty_citation_indices(self):
        with pytest.raises(ValidationError):
            EvidencedClaim(text="some claim", citation_indices=[])

    def test_accepts_valid_citation_indices(self):
        claim = EvidencedClaim(text="some claim", citation_indices=[0, 1])
        assert claim.citation_indices == [0, 1]


class TestScoredDimension:
    def test_rejects_score_below_zero(self):
        with pytest.raises(ValidationError):
            ScoredDimension(
                score=-1,
                justification=EvidencedClaim(text="test", citation_indices=[0]),
            )

    def test_rejects_score_above_five(self):
        with pytest.raises(ValidationError):
            ScoredDimension(
                score=6,
                justification=EvidencedClaim(text="test", citation_indices=[0]),
            )

    def test_accepts_valid_score(self):
        dim = ScoredDimension(
            score=3,
            justification=EvidencedClaim(text="test", citation_indices=[0]),
        )
        assert dim.score == 3


class TestValidateOutput:
    def test_valid_output_passes(self):
        citations = [_make_citation(0), _make_citation(1)]
        claim = EvidencedClaim(text="users are frustrated", citation_indices=[0])
        result = validate_output(claim, citations)
        assert result.passed

    def test_invalid_citation_index_fails(self):
        citations = [_make_citation(0)]
        claim = EvidencedClaim(text="users are frustrated", citation_indices=[5])
        result = validate_output(claim, citations)
        assert not result.passed
        assert len(result.violations) == 1
        assert "out of range" in result.violations[0].reason

    def test_invented_number_fails(self):
        citations = [_make_citation(0, excerpt="users are unhappy")]
        claim = EvidencedClaim(text="87% of users are frustrated", citation_indices=[0])
        result = validate_output(claim, citations)
        assert not result.passed
        assert any("87" in v.reason for v in result.violations)

    def test_cited_number_passes(self):
        citations = [_make_citation(0, excerpt="87% of users reported issues")]
        claim = EvidencedClaim(text="87% of users are frustrated", citation_indices=[0])
        result = validate_output(claim, citations)
        assert result.passed

    def test_small_numbers_skipped(self):
        """Numbers 0-5 are allowed (score values)."""
        citations = [_make_citation(0, excerpt="some text")]
        claim = EvidencedClaim(text="scored 3 on severity", citation_indices=[0])
        result = validate_output(claim, citations)
        assert result.passed

    def test_snapshot_excerpt_verification(self):
        citations = [_make_citation(0, excerpt="exact text from source")]
        snapshots = {
            "hash0": _make_snapshot("hash0", "This contains exact text from source and more"),
        }
        claim = EvidencedClaim(text="evidence shows issues", citation_indices=[0])
        result = validate_output(claim, citations, snapshots)
        assert result.passed

    def test_snapshot_missing_excerpt_fails(self):
        citations = [_make_citation(0, excerpt="text NOT in snapshot")]
        snapshots = {
            "hash0": _make_snapshot("hash0", "Completely different content here"),
        }
        claim = EvidencedClaim(text="evidence shows issues", citation_indices=[0])
        result = validate_output(claim, citations, snapshots)
        assert not result.passed
        assert any("Excerpt not found" in v.reason for v in result.violations)


class TestRecencyWeight:
    def test_unknown_date(self):
        from pain_radar.analysis.scoring import compute_recency_weight
        assert compute_recency_weight(None) == 0.5

    def test_recent(self):
        from pain_radar.analysis.scoring import compute_recency_weight
        w = compute_recency_weight("2026-01-01")
        assert w == 1.0

    def test_old_normal_niche(self):
        from pain_radar.analysis.scoring import compute_recency_weight
        w = compute_recency_weight("2022-01-01", "normal")
        assert w == 0.3

    def test_old_slow_niche(self):
        from pain_radar.analysis.scoring import compute_recency_weight
        w = compute_recency_weight("2022-01-01", "slow")
        assert w == 0.7
