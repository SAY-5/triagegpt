"""Retrieval quality eval: precision@k and recall over a labeled set."""

from triagegpt.eval import EvalCase, evaluate
from triagegpt.index import FailureIndex
from triagegpt.pipeline import TriagePipeline
from triagegpt.synthetic import generate_corpus, labeled_queries, novel_failure


def _index(size=400, seed=21):
    index = FailureIndex()
    index.add_all(generate_corpus(size, seed=seed))
    return index


def _cases():
    return [
        EvalCase(query=q, relevant_owner=owner, relevant_root_cause=cause)
        for q, cause, owner in labeled_queries(per_archetype=4)
    ]


def test_retrieval_precision_and_recall_above_threshold():
    score = evaluate(_index(), _cases(), k=5)
    # Every labeled query should surface at least one correct prior failure.
    assert score.recall_at_k == 1.0
    # The top neighbors should be dominated by the correct archetype.
    assert score.precision_at_k >= 0.8
    assert score.mean_reciprocal_rank >= 0.9


def test_novel_failure_yields_no_confident_match():
    pipeline = TriagePipeline(_index(), k=5)
    result = pipeline.triage(novel_failure())
    assert not result.confident_match
    assert result.suggested_owner is None
    assert result.suggested_root_cause is None


def test_empty_eval_set_scores_zero():
    score = evaluate(_index(), [], k=5)
    assert score.precision_at_k == 0.0
    assert score.recall_at_k == 0.0
