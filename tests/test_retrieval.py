import yaml

from assistant.corpus import ROOT, chunk_sections, load_docs
from assistant.retrieve import BM25, Index, tokenize
from evals.grade import has_item
from evals.retrieval import score
from assistant.pipeline import retriever

QUESTIONS = yaml.safe_load((ROOT / "evals" / "questions.yaml").read_text())


HELDOUT = yaml.safe_load((ROOT / "evals" / "heldout.yaml").read_text())


def test_eval_sets_are_well_formed():
    ids = [q["id"] for q in QUESTIONS + HELDOUT]
    assert len(ids) == len(set(ids))
    for q in QUESTIONS + HELDOUT:
        assert q["q"] and q["category"]
        assert q.get("handoff") or q.get("cite"), q["id"]  # answerable questions say what to cite


def test_every_evidence_phrase_is_in_a_current_article():
    docs = [d for d in load_docs() if d.status == "current"]
    for q in QUESTIONS + HELDOUT:
        for item in q.get("evidence", []):
            assert any(has_item(d.body, item) for d in docs), (q["id"], item)


def test_tokenize_keeps_codes_and_drops_stopwords():
    assert tokenize("What does E3001 mean for tfx_live_ and payment.failed?") == [
        "e3001", "mean", "tfx_live_", "payment.failed"]


def test_bm25_finds_exact_error_codes():
    chunks = chunk_sections(load_docs())
    scores = BM25([c.text for c in chunks]).scores("E2010")
    assert chunks[max(range(len(chunks)), key=scores.__getitem__)].doc == "api-errors"


def test_hybrid_retrieval_beats_the_naive_setup():
    v1, v2 = score(retriever("v1"), 4), score(retriever("v2"), 6)
    assert v2["evidence"] > v1["evidence"]
    assert v2["evidence"] >= v2["n"] - 2


def test_keyword_search_finds_table_rows_embeddings_miss():
    idx = Index(chunk_sections(load_docs()), "hybrid")
    assert "plans-and-pricing" in {c.doc for c in idx.search("How many invoices can I send each month on Starter?", 6)}
