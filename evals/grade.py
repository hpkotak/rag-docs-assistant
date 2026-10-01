"""Grade one answer against its eval question.

Checks, in order of what costs a business most:
  handoff   the assistant handed off exactly when it should have
  must_not  none of the forbidden text appears (outdated values, invented numbers, injected contacts)
  contradicts  none of the text that makes the answer wrong appears, even next to the right facts
  verdict   for yes/no questions, the first sentence says the right one
  facts     every expected fact appears (for handoff questions with a partial answer, the part it can answer)
  cite      the answer cites the articles the facts come from (also for the answered part of a handoff)

The outcome says what the customer experienced:
  correct            right answer, or a handoff when the docs don't cover the question
  wrong answer       answered as if sure, but the answer is wrong, outdated or incomplete
  made up            answered a question the docs don't cover, instead of handing off
  partial            gave the part it could answer, but didn't hand off the rest (or got that part wrong)
  unneeded handoff   handed off a question the docs do answer
  missing citation   right answer, but it doesn't cite the article it came from
  right, plus bad info  the right facts, but also an outdated value or text from an untrusted post
"""
import re

from assistant.corpus import doc_of


def normalize(text: str) -> str:
    text = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("*", "").replace("`", "")          # markdown bold and code
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)       # 1,000 -> 1000
    text = re.sub(r"(\$\d+)\.00(?!\d)", r"\1", text)    # $5.00 -> $5
    text = re.sub(r"[\u2010-\u2015-]", " ", text)       # hyphens and dashes -> space
    return re.sub(r"\s+", " ", text)


def contains(text: str, phrase: str) -> bool:
    """Phrase match on normalized text. Numbers must match whole: "$5" doesn't match "$50" or "$5.80"."""
    p = re.escape(normalize(phrase).strip())
    if re.match(r"[\d$]", phrase):
        p = r"(?<![\d.])" + p
    if phrase[-1].isdigit():
        p += r"(?!\d|\.\d)"
    return re.search(p, normalize(text)) is not None


def has_item(text: str, item) -> bool:
    """An item is a phrase, or a list of phrases where any one is enough."""
    return any(contains(text, p) for p in (item if isinstance(item, list) else [item]))


def contains_current(text: str, phrase: str) -> bool:
    """Ignore a value explicitly attributed to an old page; later uses still count."""
    old = (r"\b(?:old|older|archived)\s+(?:pricing\s+)?page\b[^.!?;]*?"
           r"\b(?:says|said|lists|listed)\b(?:(?!\b(?:current|now|today|but)\b)[^.!?;])*?"
           + re.escape(normalize(phrase)) + r"(?!\d|\.\d)")
    return contains(re.sub(old, "", normalize(text)), phrase)


def cites(citations: list[str], item) -> bool:
    docs = {doc_of(c) for c in citations}
    return any(d in docs for d in (item if isinstance(item, list) else [item]))


_NEGATION = re.compile(r"\b(no|not|nope|cannot|unfortunately)\b|n't\b")


def first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s|\n", normalize(text).strip(), maxsplit=1)[0]


def verdict_ok(text: str, verdict: str) -> bool:
    """For yes/no questions: the first sentence has to give the right answer, so an answer that
    mentions the right plan while saying the wrong thing ("Yes, on Growth and Scale") fails."""
    if verdict not in ("yes", "no"):  # unquoted yes/no in YAML loads as True/False
        raise ValueError(f"verdict must be the string \"yes\" or \"no\", got {verdict!r}")
    first = first_sentence(text)
    if verdict == "no":
        return bool(_NEGATION.search(first))
    return not _NEGATION.search(first) and bool(re.search(r"\b(yes|can|available|included)\b", first))


def grade(q: dict, out: dict) -> dict:
    ans = out["answer"]
    handoff_expected = bool(q.get("handoff"))
    missing = [i for i in q.get("expect", []) if not has_item(ans, i)]
    if "verdict" in q and not verdict_ok(ans, q["verdict"]):
        missing.append(f"a clear \"{q['verdict']}\" at the start")
    contradicted = [p for p in q.get("contradicts", []) if contains(ans, p)]
    forbidden = contradicted + [p for p in q.get("must_not", []) if contains(ans, p)]
    forbidden += [p for p in q.get("must_not_current", []) if contains_current(ans, p)]
    uncited = [i for i in q.get("cite", []) if not cites(out["citations"], i)]
    handoff_ok = out["handoff"] == handoff_expected

    if handoff_expected:
        ok = handoff_ok and not forbidden and not missing and not uncited
        if ok:
            outcome = "correct"
        elif handoff_ok and not forbidden and not missing:
            outcome = "missing citation"
        elif q.get("expect"):
            outcome = "partial"
        else:
            outcome = "made up"
        # A handoff question where the assistant handed off but broke a must_not still made something up.
        if handoff_ok and forbidden:
            outcome = "made up"
    else:
        ok = handoff_ok and not forbidden and not missing and not uncited
        if ok:
            outcome = "correct"
        elif out["handoff"]:
            outcome = "unneeded handoff"
        elif not missing and not forbidden:
            outcome = "missing citation"
        elif not missing and not contradicted:
            outcome = "right, plus bad info"
        else:
            outcome = "wrong answer"
    return {"pass": ok, "outcome": outcome, "missing": missing, "forbidden": forbidden,
            "uncited": uncited, "handoff_ok": handoff_ok}
