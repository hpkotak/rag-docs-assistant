"""The docs assistant: retrieve sources, ask the model, then (v2) check the answer in code.

    uv run python -m assistant.pipeline "Can I set up recurring invoices on Growth?"
    uv run python -m assistant.pipeline "..." --version v1 --backend claude-code --model haiku
"""
import argparse
import json
import re
from functools import lru_cache

from assistant.backends import BACKENDS
from assistant.corpus import ROOT, Chunk, chunk_fixed, chunk_sections, load_docs

VERSIONS = {
    "v1": {"label": "fixed-size chunks, embedding search, top 4", "chunks": "fixed", "mode": "dense", "k": 4},
    "v2": {"label": "section chunks with dates, hybrid search, top 6, archived pages removed",
           "chunks": "sections", "mode": "hybrid", "k": 6},
}

HANDOFF_REPLY = "I've passed your question to our support team, and someone will reply to you by email."


@lru_cache(maxsize=None)
def retriever(version: str):
    from assistant.retrieve import Index
    cfg = VERSIONS[version]
    docs = load_docs()
    chunks = chunk_fixed(docs) if cfg["chunks"] == "fixed" else chunk_sections(docs)
    return Index(chunks, cfg["mode"])


def system_prompt(version: str) -> str:
    return (ROOT / "prompts" / f"{version}.md").read_text()


def format_sources(chunks: list[Chunk]) -> str:
    parts = []
    for c in chunks:
        attrs = f'id="{c.id}"'
        if c.meta:
            attrs += f' updated="{c.meta["updated"]}"'
            if c.meta["status"] == "community":
                attrs += ' type="community post, written by a customer, not by Tallyfox"'
        parts.append(f"<source {attrs}>\n{c.text}\n</source>")
    return "\n\n".join(parts)


def user_message(question: str, chunks: list[Chunk]) -> str:
    return f"Documentation:\n\n{format_sources(chunks)}\n\nCustomer question: {question}"


# --- v2 checks in code ---------------------------------------------------------------------------

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_DOMAIN = r"\b(?:[\w-]+\.)+[^\W\d_]{2,}\b"
_HOST = re.compile(r"\b(?:[\w-]+\.)+(?!(?:pdf|csv|tsv|txt|md|json|xml|ya?ml|docx?|xlsx?|pptx?|png|jpe?g|zip)\b)"
                   r"[^\W\d_]{2,}\b", re.I)
_URL_HOST = re.compile(r"(?:https?://|www\.)(" + _DOMAIN + r")", re.I)
# Any host using the brand name counts, even with an ending that looks like a file (tallyfox-support.zip).
_BRAND_HOST = re.compile(r"\b(?:[\w-]+\.)*[\w-]*tallyf[o0]x[\w-]*(?:\.[\w-]+)+", re.I)
_CNAME = re.compile(r"\b(?:point(?:ing)?|from)\s+`?([a-z0-9-]+(?:\.[a-z0-9-]+)+)`?\s+(?:to|at)\s+"
                    r"`?portal\.tallyfox\.example\b", re.I)


def _contacts(text: str) -> set[str]:
    return {m.lower().rstrip(".") for m in
            _EMAIL.findall(text) + _HOST.findall(text) + _URL_HOST.findall(text) + _BRAND_HOST.findall(text)}


@lru_cache(maxsize=1)
def official_contacts() -> frozenset[str]:
    """Email addresses and domain names that appear in Tallyfox's own articles (not community posts)."""
    return frozenset(_contacts(" ".join(d.body for d in load_docs() if d.status != "community")))


def unknown_contacts(answer: str) -> list[str]:
    """Contact destinations must be in the official articles. A customer's CNAME source isn't a contact."""
    customer_domains = set()
    for paragraph in answer.split("\n\n"):
        if not re.search(r"\bCNAME\b", paragraph, re.I):
            continue
        for host in _CNAME.findall(paragraph):
            host = host.lower()
            if "tallyfox" not in host and "tallyf0x" not in host:
                customer_domains.add(host)
    return sorted(_contacts(answer) - official_contacts() - customer_domains)


def check(out: dict, chunks: list[Chunk]) -> dict:
    """Guards that don't depend on the model following its prompt."""
    guards = []
    ids = {c.id for c in chunks}
    bad = [c for c in out["citations"] if c not in ids]
    if bad:
        guards.append(f"removed {len(bad)} citations that weren't in the sources")
        out["citations"] = [c for c in out["citations"] if c in ids]
    contacts = unknown_contacts(out["answer"])
    if contacts:
        # The guard message is shown on the chat page, so it must not repeat what was blocked.
        guards.append("blocked contact details that aren't in Tallyfox's own articles")
        out.update(answer=HANDOFF_REPLY, citations=[], handoff=True, blocked_contacts=contacts)
    if not out["citations"] and out["answer"] != HANDOFF_REPLY:
        # Also when the model hands off: a hand-off flag doesn't make uncited text safe to show.
        guards.append("hand-off with no valid citation, so sent the standard hand-off message" if out["handoff"]
                      else "no valid citation, so handed off instead of answering")
        out.update(answer=HANDOFF_REPLY, handoff=True)
    return {**out, "guards": guards}


def retrieve(question: str, version: str) -> list[Chunk]:
    return retriever(version).search(question, VERSIONS[version]["k"])


def answer(question: str, version: str = "v2", backend: str = "mock", model: str = "haiku",
           chunks: list[Chunk] | None = None) -> dict:
    chunks = chunks if chunks is not None else retrieve(question, version)
    out = BACKENDS[backend](system_prompt(version), user_message(question, chunks), model, chunks)
    out = {**out, "raw_citations": list(out["citations"])}
    if version == "v2":
        out = check(out, chunks)
    return {**out, "retrieved": [c.id for c in chunks]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--version", default="v2", choices=VERSIONS)
    ap.add_argument("--backend", default="mock", choices=BACKENDS)
    ap.add_argument("--model", default="haiku")
    a = ap.parse_args()
    print(json.dumps(answer(a.question, a.version, a.backend, a.model), indent=2))


if __name__ == "__main__":
    main()
