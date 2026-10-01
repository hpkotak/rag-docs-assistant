import json

import pytest

from assistant.corpus import ROOT, Chunk
from assistant.pipeline import check
from evals.grade import contains, grade
from evals.report import load_questions

SETS = {"claude-code": None, "heldout": ROOT / "evals" / "heldout.yaml"}

Q = {"id": "x", "q": "?", "expect": ["$5"], "must_not": ["$16"], "cite": [["payment-methods", "changelog"]]}


def out(answer, citations=("payment-methods#fees",), handoff=False):
    return {"answer": answer, "citations": list(citations), "handoff": handoff}


def test_numbers_match_whole():
    assert contains("The fee is $5.", "$5")
    assert contains("The fee is $5.00", "$5")
    assert not contains("The fee is $50", "$5")
    assert not contains("The fee is $5.80", "$5")
    assert not contains("$15 a month", "5")
    assert contains("It's $1,000", "$1000")
    assert contains("5 team members", "5")


def test_normalizes_markdown_hyphens_and_quotes():
    assert contains("Use the **Retry-After** header", "retry-after")
    assert contains("Phone support isn’t available", "isn't available")
    assert contains("`tfx_live_` prefix", "tfx_live_")


def test_outcomes_for_answerable_question():
    assert grade(Q, out("It's capped at $5."))["outcome"] == "correct"
    assert grade(Q, out("0.8% of $2,000 is $16."))["outcome"] == "wrong answer"
    assert grade(Q, out("It's $5.", citations=["taxes#filing"]))["outcome"] == "missing citation"
    assert grade(Q, out("It's $5.", citations=["changelog#x"]))["pass"]  # either article is enough
    assert grade(Q, out("Passing you to support.", handoff=True))["outcome"] == "unneeded handoff"


def test_outcomes_for_handoff_questions():
    q = {"id": "sla", "q": "?", "must_not": ["99.9"], "handoff": True}
    assert grade(q, out("The docs don't say; passing you on.", handoff=True))["outcome"] == "correct"
    assert grade(q, out("We guarantee 99.9% uptime."))["outcome"] == "made up"
    assert grade(q, out("Probably 99.9%, but I've passed it on.", handoff=True))["outcome"] == "made up"
    partial = {"id": "p", "q": "?", "expect": ["$99"], "handoff": True}
    assert grade(partial, out("Scale is $99; I've asked support about the rest.", handoff=True))["pass"]
    assert grade(partial, out("Scale is $99."))["outcome"] == "partial"


def test_right_answer_that_also_quotes_an_outdated_value_still_fails():
    q = {"id": "t", "q": "?", "expect": ["$6"], "must_not": ["$10"], "cite": ["plans-and-pricing"]}
    r = grade(q, out("It's $6 (an older page says $10).", citations=["plans-and-pricing#x"]))
    assert not r["pass"] and r["outcome"] == "right, plus bad info"


def test_yes_no_questions_check_which_way_the_answer_goes():
    q = {"id": "okta", "q": "?", "verdict": "no", "expect": ["scale"], "cite": ["sso-security"]}
    wrong = out("Yes, Okta works on Growth and Scale.", citations=["sso-security#x"])
    right = out("No, not on Growth. SAML sign-in needs Scale.", citations=["sso-security#x"])
    assert not grade(q, wrong)["pass"] and grade(q, right)["pass"]
    assert grade(q, out("Unfortunately, Okta isn't available on Growth; you need Scale.",
                        citations=["sso-security#x"]))["pass"]
    yes = {"id": "rec", "q": "?", "verdict": "yes", "cite": ["changelog"]}
    assert grade(yes, out("Yes, recurring invoices are on Growth.", citations=["changelog#x"]))["pass"]
    assert not grade(yes, out("No, they're Scale only.", citations=["changelog#x"]))["pass"]


def test_every_yes_no_question_in_the_eval_sets_is_checked():
    # The check was once skipped for every "no" question: unquoted, YAML reads no as False.
    checked = [q for path in SETS.values() for q in load_questions(path) if "verdict" in q]
    assert len(checked) == 12
    for q in checked:
        wrong_way = "Yes, that's included." if q["verdict"] == "no" else "No, that isn't available."
        facts = " ".join(e if isinstance(e, str) else e[0] for e in q.get("expect", []))
        cites = [c if isinstance(c, str) else c[0] for c in q.get("cite", [])]
        r = grade(q, out(f"{wrong_way} {facts}", citations=cites))
        assert not r["pass"] and f'a clear "{q["verdict"]}" at the start' in r["missing"], q["id"]
    with pytest.raises(ValueError):
        grade({"id": "x", "q": "?", "verdict": False}, out("No."))


def test_text_that_contradicts_the_answer_makes_it_wrong():
    q = {"id": "lock", "q": "?", "expect": ["1 october 2026"], "contradicts": ["$29 on 15 october"],
         "must_not": ["$19"], "cite": ["changelog"]}
    good = "Your price changes at your first renewal after 1 October 2026."
    assert grade(q, out(good, citations=["changelog#x"]))["pass"]
    r = grade(q, out(good + " So you'd pay $29 on 15 October.", citations=["changelog#x"]))
    assert not r["pass"] and r["outcome"] == "wrong answer"
    assert grade(q, out(good + " It was once $19.", citations=["changelog#x"]))["outcome"] == "right, plus bad info"


def test_the_answered_part_of_a_handoff_needs_its_citation():
    q = {"id": "p", "q": "?", "expect": ["$99"], "cite": ["plans-and-pricing"], "handoff": True}
    answer = "Scale is $99; I've asked support about the rest."
    assert grade(q, out(answer, citations=["plans-and-pricing#intro"], handoff=True))["pass"]
    r = grade(q, out(answer, citations=[], handoff=True))
    assert not r["pass"] and r["outcome"] == "missing citation"


@pytest.mark.parametrize("folder", ["claude-code", "heldout"])
def test_current_code_checks_leave_the_saved_grades_unchanged(folder):
    # The checks in assistant/pipeline.py were tightened after these answers were collected. Replaying
    # them over what the model returned must not change any grade, or the saved results would no longer
    # describe the current code.
    questions = {q["id"]: q for q in load_questions(SETS[folder])}
    for line in (ROOT / "results" / folder / "results.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "error" in r or r["version"] != "v2":
            continue
        assert not r["guards"]  # so the saved answer is what the model returned
        replayed = check({"answer": r["answer"], "citations": list(r["raw_citations"]), "handoff": r["handoff"]},
                         [Chunk(i, i.split("#")[0], "") for i in r["retrieved"]])
        q = questions[r["question"]]
        assert grade(q, replayed)["outcome"] == grade(q, r)["outcome"], (r["model"], r["question"], r["trial"])
