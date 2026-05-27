"""Contract tests for the core invariants of the triage pipeline."""

from triagegpt.index import FailureIndex
from triagegpt.pipeline import TriagePipeline
from triagegpt.providers import DeterministicSummaryProvider
from triagegpt.suggest import suggest
from triagegpt.synthetic import generate_corpus, generate_query


def _index(size=200, seed=7):
    index = FailureIndex()
    index.add_all(generate_corpus(size, seed=seed))
    return index


def test_summary_is_always_valid():
    summarizer = DeterministicSummaryProvider()
    for i in range(50):
        failure = generate_query(i % 5, seed=1000 + i)
        assert summarizer.summarize(failure).is_valid()


def test_retrieval_returns_k_ranked_neighbors():
    index = _index()
    neighbors = index.query(generate_query(0), k=5)
    assert len(neighbors) == 5
    sims = [n.similarity for n in neighbors]
    assert sims == sorted(sims, reverse=True)


def test_identical_failure_retrieves_itself_first():
    index = FailureIndex()
    corpus = generate_corpus(40, seed=3)
    index.add_all(corpus)
    target = corpus[10]
    top = index.query(target, k=1)[0]
    assert top.failure.signature() == target.signature()
    assert top.similarity > 0.999


def test_suggestion_is_grounded_in_neighbors():
    index = _index()
    pipeline = TriagePipeline(index, k=5)
    result = pipeline.triage(generate_query(2))
    assert result.confident_match
    neighbor_owners = {n.failure.owner for n in result.neighbors}
    neighbor_causes = {n.failure.root_cause for n in result.neighbors}
    assert result.suggested_owner in neighbor_owners
    assert result.suggested_root_cause in neighbor_causes


def test_no_neighbors_yields_no_confident_match():
    summary = DeterministicSummaryProvider().summarize(generate_query(0))
    result = suggest(summary, generate_query(0), neighbors=[])
    assert not result.confident_match
    assert result.suggested_owner is None
