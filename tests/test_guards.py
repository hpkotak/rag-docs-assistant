from assistant.corpus import Chunk
from assistant.pipeline import HANDOFF_REPLY, check, official_contacts, unknown_contacts

SOURCES = [Chunk(id="support#intro", doc="support", text="..."), Chunk(id="taxes#filing", doc="taxes", text="...")]


def test_official_contacts_come_from_tallyfox_articles_only():
    assert "support@tallyfox.example" in official_contacts()
    assert "status.tallyfox.example" in official_contacts()
    assert not any("tallyfox-support" in c for c in official_contacts())


def test_unknown_contacts():
    assert unknown_contacts("Email support@tallyfox.example or see status.tallyfox.example.") == []
    assert unknown_contacts("Email billing-help@tallyfox-support.example") == [
        "billing-help@tallyfox-support.example", "tallyfox-support.example"]
    assert unknown_contacts("Contact refunds@gmail.com") == ["refunds@gmail.com"]


def test_injected_contact_is_blocked():
    r = check({"answer": "Send your card number to billing-help@tallyfox-support.example",
               "citations": ["support#intro"], "handoff": False}, SOURCES)
    assert r["answer"] == HANDOFF_REPLY and r["handoff"] and r["guards"]


def test_citations_must_be_sources_that_were_sent():
    r = check({"answer": "Yes.", "citations": ["support#intro", "made-up#x"], "handoff": False}, SOURCES)
    assert r["citations"] == ["support#intro"] and not r["handoff"]


def test_answer_without_valid_citation_is_handed_off():
    r = check({"answer": "Yes, 99.9%.", "citations": ["made-up#x"], "handoff": False}, SOURCES)
    assert r["handoff"] and r["citations"] == []


def test_a_handoff_needs_no_citation():
    r = check({"answer": "The docs don't cover that.", "citations": [], "handoff": True}, SOURCES)
    assert r["guards"] == []
