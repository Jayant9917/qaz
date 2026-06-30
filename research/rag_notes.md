# RAG Research Notes

**Status:** Active research notebook
**Normative specification:** docs/capabilities/06_RAG_ARCHITECTURE.md

## Purpose

Record parser, chunking, embedding, retrieval, reranking, grounding, and evaluation experiments.

## Research topics

- Parser quality by file type
- Chunk size and overlap
- PostgreSQL lexical configuration
- Embedding quality/cost/privacy
- Milvus metric/index
- Hybrid fusion
- Local reranker
- Citation/grounding validator
- Fast/Deep retrieval budgets
- Graph RAG contribution
- Free-model grounding reliability

## Evaluation

Use versioned representative and adversarial queries. Measure retrieval precision/recall, citation correctness/completeness, faithfulness, conflict disclosure, latency, cost, and deletion correctness.

## Constraint

No experiment may treat derived indexes as authority or bypass canonical PostgreSQL reauthorization.
