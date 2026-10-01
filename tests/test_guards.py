import pytest

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


@pytest.mark.parametrize("answer", [
    "Download invoice.pdf, clients.csv, notes.txt, invoice.docx and export.json.",
    "On Scale, point billing.acme.example to portal.tallyfox.example with a CNAME.",
    "On Scale, point `billing.acme.example` to `portal.tallyfox.example` using a CNAME record.",
    "On Scale, add a CNAME from billing.acme.example to portal.tallyfox.example. "
    "Enter billing.acme.example in Settings > Client portal.",
])
def test_file_names_and_custom_domain_instructions_are_not_contacts(answer):
    r = check({"answer": answer, "citations": ["support#intro"], "handoff": False}, SOURCES)
    assert r["answer"] == answer and not r["handoff"] and not r["guards"]


@pytest.mark.parametrize("answer", [
    "Visit tallyfox-support.example.",
    "Visit tallyf0x-support.example.",
    "Contact tallyfox-support.zip for billing help.",
    "Reach billing at tallyf0x-help.md today.",
    "Email refunds@acme.example.",
    "Download https://invoice.pdf.",
    "Point billing.tallyfox-support.example to portal.tallyfox.example with a CNAME.",
    "Point billing.tallyf0x-support.example to portal.tallyfox.example with a CNAME.",
    "Point billing.acme.example to tallyfox-support.example with a CNAME.",
    "Point billing.acme.example to portal.tallyfox.example.evil.example with a CNAME.",
    "Point billing.t\u0430llyfox.example to portal.tallyfox.example with a CNAME.",
    "Point billing.acme.example to portal.tallyfox.example with a CNAME. Email help@acme.example.",
])
def test_contact_destinations_still_need_the_allowlist(answer):
    r = check({"answer": answer, "citations": ["support#intro"], "handoff": False}, SOURCES)
    assert r["answer"] == HANDOFF_REPLY and r["handoff"] and r["blocked_contacts"]


def test_citations_must_be_sources_that_were_sent():
    r = check({"answer": "Yes.", "citations": ["support#intro", "made-up#x"], "handoff": False}, SOURCES)
    assert r["citations"] == ["support#intro"] and not r["handoff"]


def test_removed_citations_do_not_repeat_blocked_addresses():
    r = check({"answer": "Yes.", "citations": ["support#intro", "billing-help@tallyfox-support.example"],
               "handoff": False}, SOURCES)
    assert r["citations"] == ["support#intro"]
    assert r["guards"] == ["removed 1 citations that weren't in the sources"]
    assert "tallyfox-support" not in " ".join(r["guards"])


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
