from assistant.corpus import chunk_fixed, chunk_sections, doc_of, load_docs

DOCS = load_docs()


def test_front_matter():
    by = {d.slug: d for d in DOCS}
    assert by["pricing-2025"].status == "archived"
    assert by["community-tips"].status == "community"
    assert by["plans-and-pricing"].updated == "2026-07-01"
    assert by["api-authentication"].title == "API: authentication"


def test_sections_leave_out_archived_pages_and_keep_dates():
    chunks = chunk_sections(DOCS)
    assert not any(c.doc == "pricing-2025" for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)
    c = next(c for c in chunks if c.id == "plans-and-pricing#annual-billing")
    assert c.text.startswith("Plans and pricing > Annual billing")
    assert c.meta["updated"] == "2026-07-01"


def test_fixed_chunks_overlap_and_include_everything():
    chunks = chunk_fixed(DOCS, size=600, overlap=100)
    assert any(c.doc == "pricing-2025" for c in chunks)
    a, b = [c for c in chunks if c.doc == "plans-and-pricing"][:2]
    assert a.text[-100:] == b.text[:100]


def test_doc_of():
    assert doc_of("plans-and-pricing#annual-billing") == "plans-and-pricing"
    assert doc_of("pricing-2025.md:0") == "pricing-2025"
    assert doc_of("taxes.md") == "taxes"
