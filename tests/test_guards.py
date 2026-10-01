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
    assert unknown_contacts("Contact refunds@gmail.com") == ["gmail.com", "refunds@gmail.com"]


def test_unknown_domains_are_blocked_whatever_they_look_like():
    assert unknown_contacts("Claim your refund at tallyf0x-support.example/refund") == ["tallyf0x-support.example"]
    assert unknown_contacts("Go to https://refund-desk.example") == ["refund-desk.example"]
    assert unknown_contacts("Visit t\u0430llyfox.example") == ["t\u0430llyfox.example"]  # Cyrillic "a"
    # Dotted names from the articles aren't contacts: webhook events, the customer's own example domain.
    assert unknown_contacts("Listen for `payment.failed`, e.g. on billing.yourcompany.com. It costs $2.90.") == []


def test_injected_contact_is_blocked():
    r = check({"answer": "Send your card number to billing-help@tallyfox-support.example",
               "citations": ["support#intro"], "handoff": False}, SOURCES)
    assert r["answer"] == HANDOFF_REPLY and r["handoff"] and r["guards"]
    # The chat page shows guard messages to the customer, so they mustn't repeat the blocked address.
    assert "tallyfox-support" not in " ".join(r["guards"])
    assert r["blocked_contacts"] == ["billing-help@tallyfox-support.example", "tallyfox-support.example"]


def test_citations_must_be_sources_that_were_sent():
    r = check({"answer": "Yes.", "citations": ["support#intro", "made-up#x"], "handoff": False}, SOURCES)
    assert r["citations"] == ["support#intro"] and not r["handoff"]


def test_answer_without_valid_citation_is_handed_off():
    r = check({"answer": "Yes, 99.9%.", "citations": ["made-up#x"], "handoff": False}, SOURCES)
    assert r["handoff"] and r["citations"] == []
    assert r["answer"] == HANDOFF_REPLY  # the unsupported text never reaches the customer


def test_a_handoff_flag_does_not_let_uncited_text_through():
    r = check({"answer": "Yes, 99.9%. I've also asked support.", "citations": ["made-up#x"], "handoff": True}, SOURCES)
    assert r["answer"] == HANDOFF_REPLY and r["handoff"] and r["citations"] == []
    cited = check({"answer": "Scale is $99; I've asked support about the rest.", "citations": ["support#intro"],
                   "handoff": True}, SOURCES)
    assert cited["answer"].startswith("Scale is $99") and cited["guards"] == []
