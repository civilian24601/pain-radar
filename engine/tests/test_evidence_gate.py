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


class TestComputeClusterConfidence:
    def test_single_citation_low_confidence(self):
        """A single citation from one domain/type should produce low confidence."""
        from pain_radar.analysis.scoring import compute_cluster_confidence
        citations = [_make_citation(0)]
        conf = compute_cluster_confidence([0], citations)
        assert conf < 0.4, f"Expected < 0.4, got {conf}"

    def test_diverse_citations_high_confidence(self):
        """3 citations, 3 domains, 3 source types should produce high confidence."""
        from pain_radar.analysis.scoring import compute_cluster_confidence
        citations = [
            Citation(
                url="https://reddit.com/r/test/1",
                excerpt="pain point A",
                source_type=SourceType.REDDIT,
                date_published="2026-01-01",
                date_retrieved="2026-01-15T00:00:00Z",
                recency_months=0,
                snapshot_hash="hashA",
            ),
            Citation(
                url="https://g2.com/review/1",
                excerpt="pain point B",
                source_type=SourceType.REVIEW,
                date_published="2026-01-01",
                date_retrieved="2026-01-15T00:00:00Z",
                recency_months=0,
                snapshot_hash="hashB",
            ),
            Citation(
                url="https://news.ycombinator.com/item?id=1",
                excerpt="pain point C",
                source_type=SourceType.WEB,
                date_published="2026-01-01",
                date_retrieved="2026-01-15T00:00:00Z",
                recency_months=0,
                snapshot_hash="hashC",
            ),
        ]
        conf = compute_cluster_confidence([0, 1, 2], citations)
        assert conf > 0.6, f"Expected > 0.6, got {conf}"

    def test_empty_indices_returns_zero(self):
        from pain_radar.analysis.scoring import compute_cluster_confidence
        citations = [_make_citation(0)]
        assert compute_cluster_confidence([], citations) == 0.0

    def test_out_of_range_indices_ignored(self):
        from pain_radar.analysis.scoring import compute_cluster_confidence
        citations = [_make_citation(0)]
        conf = compute_cluster_confidence([0, 99], citations)
        # Should behave like single citation
        assert conf < 0.4


class TestRelevanceFiltering:
    def test_relevance_stopword_filtering(self):
        """The word 'quote' alone should not mark career threads as on-topic."""
        from pain_radar.pipeline.relevance import compute_topic_relevance
        citations = [
            Citation(
                url="https://reddit.com/r/careers/1",
                excerpt="Here is a motivational quote about entrepreneurship",
                source_type=SourceType.REDDIT,
                date_published=None,
                date_retrieved="2026-01-01T00:00:00Z",
                recency_months=None,
                snapshot_hash="hash_career",
            ),
        ]
        # Keyword "quote" is a stopword — should not match
        result = compute_topic_relevance(citations, [], ["quote"])
        assert len(result.off_topic_indices) == 1
        assert len(result.on_topic_indices) == 0

    def test_multi_keyword_requirement(self):
        """With 3+ keywords, a single match should be insufficient."""
        from pain_radar.pipeline.relevance import compute_topic_relevance
        citations = [
            Citation(
                url="https://example.com/1",
                excerpt="This article discusses invoice processing in detail",
                source_type=SourceType.WEB,
                date_published=None,
                date_retrieved="2026-01-01T00:00:00Z",
                recency_months=None,
                snapshot_hash="hash_single",
            ),
        ]
        # 3 keywords, but text only matches "invoice" — should be off-topic
        result = compute_topic_relevance(
            citations, [],
            ["invoice automation", "accounts payable", "bookkeeper"],
        )
        assert len(result.off_topic_indices) == 1
        assert len(result.on_topic_indices) == 0

    def test_multi_keyword_two_matches_on_topic(self):
        """With 3+ keywords and 2 matches, should be on-topic."""
        from pain_radar.pipeline.relevance import compute_topic_relevance
        citations = [
            Citation(
                url="https://example.com/1",
                excerpt="This article discusses invoice automation and bookkeeper workflows",
                source_type=SourceType.WEB,
                date_published=None,
                date_retrieved="2026-01-01T00:00:00Z",
                recency_months=None,
                snapshot_hash="hash_multi",
            ),
        ]
        result = compute_topic_relevance(
            citations, [],
            ["invoice automation", "accounts payable", "bookkeeper"],
        )
        assert len(result.on_topic_indices) == 1


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
