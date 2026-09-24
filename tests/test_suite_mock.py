"""The whole eval suite against the offline mock model, which copies the top source and never hands off.

This checks the plumbing and the code guards, not answer quality: whatever the mock copies, the v2
guards must stop injected contact details and uncited answers from reaching the customer.
"""
import yaml

from assistant.corpus import ROOT, Chunk, chunk_fixed, chunk_sections, load_docs
from assistant.pipeline import answer, unknown_contacts
from evals.grade import grade

QUESTIONS = yaml.safe_load((ROOT / "evals" / "questions.yaml").read_text())


def run(version):
    return [(q, answer(q["q"], version, "mock")) for q in QUESTIONS]


def test_v2_never_shows_unknown_contact_details():
    for q, out in run("v2"):
        assert unknown_contacts(out["answer"]) == [], q["id"]
        assert set(out["citations"]) <= set(out["retrieved"])


def test_only_the_v2_guard_stops_the_injected_address():
    # Give both versions the community post with the planted instruction as their only source.
    post = next(c for c in chunk_sections(load_docs()) if c.id.startswith("community-tips#refunds"))
    fixed = [c for c in chunk_fixed(load_docs(), size=10_000) if c.doc == "community-tips"]
    assert unknown_contacts(answer("Refund?", "v1", "mock", chunks=[Chunk(fixed[0].id, "community-tips",
                                                                             post.text)])["answer"])
    v2 = answer("Refund?", "v2", "mock", chunks=[post])
    assert unknown_contacts(v2["answer"]) == [] and v2["handoff"]


def test_grades_are_deterministic():
    a = [grade(q, out)["outcome"] for q, out in run("v2")]
    b = [grade(q, out)["outcome"] for q, out in run("v2")]
    assert a == b
