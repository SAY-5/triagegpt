from triagegpt.index import FailureIndex
from triagegpt.models import TestFailure
from triagegpt.pipeline import TriagePipeline
from triagegpt.providers import DeterministicSummaryProvider, HashingEmbeddingProvider
from triagegpt.synthetic import generate_corpus, generate_query


def test_summary_extracts_error_type():
    failure = TestFailure(
        test_id="tests/test_pay.py::test_capture",
        message="TimeoutException: gateway stub did not respond in 10s",
        log_text="FAILED tests/test_pay.py::test_capture - TimeoutException: stub timeout",
    )
    summary = DeterministicSummaryProvider().summarize(failure)
    assert summary.error_type == "TimeoutException"
    assert summary.is_valid()


def test_embedding_is_normalized_and_stable():
    embedder = HashingEmbeddingProvider(dim=64)
    v1 = embedder.embed("connection pool exhausted")
    v2 = embedder.embed("connection pool exhausted")
    assert v1 == v2
    assert abs(sum(x * x for x in v1) - 1.0) < 1e-9


def test_pipeline_suggests_owner_for_known_archetype():
    index = FailureIndex()
    index.add_all(generate_corpus(150, seed=1))
    pipeline = TriagePipeline(index, k=5)

    # archetype 0 is the database connection pool family owned by data-platform
    result = pipeline.triage(generate_query(0))
    assert result.confident_match
    assert result.suggested_owner == "data-platform"
