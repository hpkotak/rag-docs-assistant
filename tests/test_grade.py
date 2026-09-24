from evals.grade import contains, grade

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
