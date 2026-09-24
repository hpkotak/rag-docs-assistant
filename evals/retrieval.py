"""Retrieval-only check: do the sources sent to the model contain what the answer needs?

    uv run python -m evals.retrieval

Two measures, over the questions the docs can answer:
  articles  the sources include the articles the answer should cite
  evidence  the exact text the answer depends on is inside one of the sources, not cut in half
            between two chunks and not missing

No model is involved, so this runs offline and gives the same numbers every time.
"""
import os
import sys

import yaml

from assistant.corpus import ROOT, chunk_fixed, chunk_sections, load_docs
from assistant.pipeline import VERSIONS, retriever
from evals.grade import cites, has_item

QUESTIONS = yaml.safe_load((ROOT / "evals" / "questions.yaml").read_text())


def score(index, k: int) -> dict:
    cases = [q for q in QUESTIONS if q.get("evidence")]
    art_miss, ev_miss = [], []
    for q in cases:
        chunks = index.search(q["q"], k)
        if not all(cites([c.doc for c in chunks], item) for item in q["cite"]):
            art_miss.append(q["id"])
        if not all(any(has_item(c.text, item) for c in chunks) for item in q["evidence"]):
            ev_miss.append(q["id"])
    return {"n": len(cases), "articles": len(cases) - len(art_miss), "evidence": len(cases) - len(ev_miss),
            "articles_missed": art_miss, "evidence_missed": ev_miss}


def configs() -> list[tuple[str, object, int]]:
    from assistant.retrieve import Index
    docs = load_docs()
    rows = [(f"{v}: {cfg['label']}", retriever(v), cfg["k"]) for v, cfg in VERSIONS.items()]
    # One change at a time, to see what each part of v2 contributes.
    return rows + [("fixed-size chunks, hybrid search, top 6", Index(chunk_fixed(docs), "hybrid"), 6),
                   ("section chunks, embedding search, top 6", Index(chunk_sections(docs), "dense"), 6),
                   ("section chunks, keyword search, top 6", Index(chunk_sections(docs), "bm25"), 6),
                   ("section chunks, hybrid search, top 4", Index(chunk_sections(docs), "hybrid"), 4)]


def main():
    for label, index, k in configs():
        r = score(index, k)
        print(f"articles {r['articles']}/{r['n']}  evidence {r['evidence']}/{r['n']}  {label}")
        if r["evidence_missed"]:
            print(f"    evidence missed: {', '.join(r['evidence_missed'])}")
    sys.stdout.flush()
    os._exit(0)  # onnxruntime can crash while Python shuts down; the work is done by now


if __name__ == "__main__":
    main()
