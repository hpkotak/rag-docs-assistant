"""Load the help center and split it into chunks.

v1 splits every file into fixed-size windows of text, the default in most RAG tutorials.
v2 splits on headings, so each chunk is one section with its article title, date and status attached,
and leaves archived articles out of the index.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


@dataclass
class Doc:
    slug: str
    title: str
    updated: str
    status: str  # "current", "archived" or "community"
    body: str


@dataclass
class Chunk:
    id: str
    doc: str  # slug of the article it came from
    text: str
    meta: dict = field(default_factory=dict)


def load_docs(folder: Path = DOCS) -> list[Doc]:
    docs = []
    for path in sorted(folder.glob("*.md")):
        raw = path.read_text()
        m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
        front = dict(line.split(": ", 1) for line in m.group(1).splitlines()) if m else {}
        docs.append(Doc(slug=path.stem, title=front.get("title", path.stem).strip('"'),
                        updated=front.get("updated", ""), status=front.get("status", "current"),
                        body=raw[m.end():] if m else raw))
    return docs


def chunk_fixed(docs: list[Doc], size: int = 600, overlap: int = 100) -> list[Chunk]:
    """Fixed windows of characters with some overlap. No titles, dates or section boundaries."""
    chunks = []
    for d in docs:
        text, start, i = d.body.strip(), 0, 0
        while start < len(text):
            chunks.append(Chunk(id=f"{d.slug}.md:{i}", doc=d.slug, text=text[start:start + size]))
            start += size - overlap
            i += 1
    return chunks


def _slugify(heading: str) -> str:
    words = re.findall(r"[a-z0-9]+", heading.lower())
    return "-".join(words[:6])


def chunk_sections(docs: list[Doc], include_archived: bool = False) -> list[Chunk]:
    """One chunk per section (## heading). The text before the first ## heading is its own chunk."""
    chunks = []
    for d in docs:
        if d.status == "archived" and not include_archived:
            continue
        parts = re.split(r"^## (.+)$", d.body, flags=re.M)
        intro = re.sub(r"^# .+$", "", parts[0], flags=re.M).strip()
        sections = [("", intro)] if intro else []
        sections += [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts), 2)]
        for heading, body in sections:
            title = f"{d.title} > {heading}" if heading else d.title
            chunks.append(Chunk(id=f"{d.slug}#{_slugify(heading) or 'intro'}", doc=d.slug,
                                text=f"{title}\n\n{body}",
                                meta={"title": title, "updated": d.updated, "status": d.status}))
    return chunks


def doc_of(citation: str) -> str:
    """Article slug for a citation, which may be a chunk id from either version or a file name."""
    return re.split(r"[#:]", citation.strip())[0].removesuffix(".md")
