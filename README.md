# TriageGPT

A defect triage and log summarization tool for CI. It ingests failing test
logs, summarizes each failure into a structured form, retrieves similar past
failures from an embeddings index, and suggests a likely root cause and owner.
Results are emitted as JSON and as a Markdown comment that a pipeline step can
post automatically.

The tool is fully offline. The summarization and embedding layers sit behind a
provider seam with deterministic local defaults, so the whole pipeline runs
hermetically with no network access.

## How it works

1. Ingest: parse failing test logs in a couple of common CI formats (pytest
   short summaries and JUnit style text dumps), or generate a synthetic corpus
   of runs with seeded failures.
2. Summarize: a summarization provider turns a failing log into a structured
   summary (error type, headline, key lines).
3. Retrieve: an embeddings index over past failures returns the k most similar
   prior failures, ranked by cosine similarity.
4. Suggest: the retrieved neighbors carry known root cause and owner labels.
   The suggester aggregates them into a ranked owner suggestion with a
   confidence, grounded only in the retrieved neighbors.
5. Post: the result is rendered to JSON and to a Markdown comment so a CI step
   can attach it to the failing run.

When no retrieved failure clears the similarity floor, or the aggregated owner
confidence is too low, the tool reports `no confident match` rather than
forcing a wrong owner.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
triagegpt path/to/failing.log --format markdown
triagegpt path/to/failing.log --format json --out triage.json
```

The CLI parses the first failure in the log, builds a synthetic corpus of past
failures, retrieves neighbors, and prints the report.

## Posting into CI

The provided GitHub Actions workflow runs the tool on a sample log and uploads
the rendered Markdown as a build artifact. A pipeline can instead pipe the
Markdown into a pull request comment or a check run payload. Because the
provider layer is deterministic, the emitted artifact is stable for a given
input.

## The model provider seam

`triagegpt.providers` defines two protocols: `SummaryProvider` and
`EmbeddingProvider`. The defaults are `DeterministicSummaryProvider` (extracts
the error type and salient log lines) and `HashingEmbeddingProvider` (a signed
feature hashing embedding whose cosine similarity tracks token overlap). A
network backed provider can be dropped in behind the same protocols without
changing the index, suggester, or reporting code.

## Retrieval quality

`tests/test_retrieval_quality.py` runs a small labeled eval set of queries with
known correct prior failures and computes precision@k and recall@k. On the
20 case labeled set over a 400 failure corpus the current retrieval scores
precision@5 1.0, recall@5 1.0 and mean reciprocal rank 1.0; the test asserts
recall@5 of 1.0, precision@5 at least 0.8 and MRR at least 0.9. It also checks
the novel failure path, where a failure unlike any archetype yields
`no confident match` rather than a forced owner.

## How this differs from `tracesift`

`triagegpt` is the model assisted triage path: a summarization provider plus an
embeddings retrieval index over past failures, an owner suggestion aggregated
from retrieved neighbors, and a CI auto-post step. `tracesift` is the
deterministic offline clustering tool that groups failures by structural
signature with no model layer. Both triage failures, by different mechanisms:
triagegpt retrieves and ranks similar prior failures through embeddings and a
provider seam, while tracesift clusters them deterministically.

## Development

```bash
ruff check .
mypy
pytest --cov=triagegpt
```

## License

MIT
