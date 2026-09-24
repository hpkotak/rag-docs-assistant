"""Turn results.jsonl into summary.json and REPORT.md."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import yaml

from assistant.corpus import ROOT
from evals.grade import grade

QUESTIONS = yaml.safe_load((ROOT / "evals" / "questions.yaml").read_text())
CATEGORIES = list(dict.fromkeys(q["category"] for q in QUESTIONS))
OUTCOMES = ["wrong answer", "made up", "right, plus bad info", "partial", "unneeded handoff", "missing citation"]


def load(out: Path) -> list[dict]:
    """Saved answers, regraded against the current eval set (dropping questions no longer in it)."""
    by_id = {q["id"]: q for q in QUESTIONS}
    rows = {}
    for line in (out / "results.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["question"] not in by_id:
            continue
        if "error" not in r:
            r.update(grade(by_id[r["question"]], r))
        key = (r["model"], r["version"], r["question"], r["trial"])
        if "error" not in r or key not in rows:  # a successful retry replaces an earlier error
            rows[key] = r
    return list(rows.values())


def summarise(rows: list[dict]) -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["version"])].append(r)
    summary = {}
    for (model, version), rs in sorted(groups.items()):
        ok = [r for r in rs if "error" not in r]
        by_q = defaultdict(list)
        for r in ok:
            by_q[r["question"]].append(r["pass"])
        outcomes = Counter(r["outcome"] for r in ok)
        by_cat = defaultdict(list)
        for r in ok:
            by_cat[r["category"]].append(r["pass"])
        summary[f"{model}/{version}"] = {
            "model": model, "version": version, "answers": len(ok), "errors": len(rs) - len(ok),
            "pass_rate": round(sum(r["pass"] for r in ok) / len(ok), 3) if ok else 0,
            "questions": len(by_q),
            "all_trials_pass": sum(all(v) for v in by_q.values()),
            "trials": max((len(v) for v in by_q.values()), default=0),
            "outcomes": {o: outcomes.get(o, 0) for o in OUTCOMES},
            # Answers a customer would act on that are wrong: the costly failure for a support bot.
            "confidently_wrong": outcomes.get("wrong answer", 0) + outcomes.get("made up", 0),
            "stale_answers": sum(1 for r in ok if r["category"] == "stale" and not r["pass"] and not r["handoff"]),
            "injected_contact_shown": sum(1 for r in ok if r["category"] == "injection" and r["forbidden"]),
            "cited_archived_page": sum(1 for r in ok if any(c.startswith("pricing-2025") for c in r["citations"])),
            "guards_fired": sum(1 for r in ok if r.get("guards")),
            "by_category": {c: round(sum(v) / len(v), 3) for c, v in by_cat.items()},
            "cost_per_answer": round(sum(r["cost_usd"] for r in ok) / len(ok), 5) if ok else 0,
            "median_seconds": round(median(r["duration_ms"] for r in ok) / 1000, 1) if ok else 0,
            "model_ids": sorted({m for r in ok for m in r.get("model_ids", [])}),
        }
    return summary


def pct(x: float) -> str:
    return f"{round(100 * x)}%"


def md_report(summary: dict, rows: list[dict]) -> str:
    keys = list(summary)
    lines = ["# Docs assistant eval results", ""]
    lines += ["| Setup | Correct (single answers) | Questions correct in every run | Confidently wrong | "
              "Outdated answers | Cited the archived 2025 pricing page | Injected contact shown | Unneeded handoffs | "
              "Cost per answer | Median time |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, s in summary.items():
        lines.append(f"| {k} | {pct(s['pass_rate'])} ({s['answers']} answers) | {s['all_trials_pass']}/{s['questions']} "
                     f"| {s['confidently_wrong']} | {s['stale_answers']} | {s['cited_archived_page']} | {s['injected_contact_shown']} "
                     f"| {s['outcomes']['unneeded handoff']} | ${s['cost_per_answer']:.4f} | {s['median_seconds']}s |")
    lines += ["", "## Outcomes", "", "| Setup | " + " | ".join(OUTCOMES) + " | v2 guards fired | errors |",
              "| --- |" + " --- |" * (len(OUTCOMES) + 2)]
    for k, s in summary.items():
        lines.append(f"| {k} | " + " | ".join(str(s["outcomes"][o]) for o in OUTCOMES)
                     + f" | {s['guards_fired']} | {s['errors']} |")
    lines += ["", "## By category (share of single answers correct)", "",
              "| Category | " + " | ".join(keys) + " |", "| --- |" + " --- |" * len(keys)]
    for c in CATEGORIES:
        lines.append(f"| {c} | " + " | ".join(pct(summary[k]["by_category"].get(c, 0)) for k in keys) + " |")

    by = defaultdict(list)
    for r in rows:
        if "error" not in r:
            by[(r["question"], f"{r['model']}/{r['version']}")].append(r)
    lines += ["", "## By question (runs correct)", "", "| Question | Category | " + " | ".join(keys) + " |",
              "| --- | --- |" + " --- |" * len(keys)]
    for q in QUESTIONS:
        cells = []
        for k in keys:
            rs = by.get((q["id"], k), [])
            cells.append(f"{sum(r['pass'] for r in rs)}/{len(rs)}" if rs else "-")
        lines.append(f"| {q['id']} | {q['category']} | " + " | ".join(cells) + " |")

    lines += ["", "## Example failures", "", "One failing answer per question and setup.", ""]
    for q in QUESTIONS:
        shown = []
        for k in keys:
            bad = [r for r in by.get((q["id"], k), []) if not r["pass"]]
            if bad:
                r = bad[0]
                why = [f"missing {m}" for m in r["missing"]] + [f"contains {f!r}" for f in r["forbidden"]]
                why += [f"doesn't cite {u}" for u in r["uncited"]]
                if not r["handoff_ok"]:
                    why.append("handed off" if r["handoff"] else "didn't hand off")
                ans = r["answer"].replace("\n", " ")
                shown.append(f"- **{k}**, {r['outcome']} ({len(bad)} of {len(by[(q['id'], k)])} runs failed; "
                             f"{'; '.join(why)}): {ans[:400]}{'...' if len(ans) > 400 else ''}")
                if r.get("guards"):
                    shown.append(f"  - v2 guard: {'; '.join(r['guards'])}")
        if shown:
            lines += [f"### {q['id']}: {q['q']}", ""] + shown + [""]
    return "\n".join(lines) + "\n"


def write(out: Path):
    rows = load(out)
    summary = summarise(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "REPORT.md").write_text(md_report(summary, rows))
    for k, s in summary.items():
        print(f"{k}: {pct(s['pass_rate'])} correct, {s['all_trials_pass']}/{s['questions']} correct in every run, "
              f"{s['confidently_wrong']} confidently wrong, {s['errors']} errors")


if __name__ == "__main__":
    import sys
    write(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "results" / "claude-code"))
