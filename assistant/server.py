"""Chat page for the docs assistant, with an option to compare the two versions side by side.

    uv run python -m assistant.server                          # real model via the Claude Code CLI
    uv run python -m assistant.server --backend mock           # offline
Then open http://localhost:8000
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from assistant.backends import BACKENDS
from assistant.corpus import load_docs
from assistant.pipeline import VERSIONS, answer, retriever

STATIC = Path(__file__).parent / "static"
TITLES = {d.slug: d.title for d in load_docs()}


def describe(citation: str) -> dict:
    """A citation id as the customer sees it: article title, and the section when there is one."""
    slug, _, section = citation.replace(".md:", "#").partition("#")
    label = TITLES.get(slug, slug)
    if section and not section.isdigit():
        label += " > " + section.replace("-", " ").capitalize()
    return {"id": citation, "label": label, "archived": slug == "pricing-2025"}


def make_handler(backend: str, model: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/", "/index.html"):
                return self.send_error(404)
            body = (STATIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/api/ask":
                return self.send_error(404)
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            question = str(req.get("question", "")).strip()[:500]
            versions = [v for v in req.get("versions", ["v2"]) if v in VERSIONS] or ["v2"]
            with ThreadPoolExecutor(len(versions)) as pool:
                outs = dict(zip(versions, pool.map(lambda v: answer(question, v, backend, model), versions)))
            reply = {v: {"answer": o["answer"], "handoff": o["handoff"], "guards": o.get("guards", []),
                         "citations": [describe(c) for c in o["citations"]],
                         "seconds": round(o["duration_ms"] / 1000, 1)} for v, o in outs.items()}
            body = json.dumps({"model": model, "backend": backend, "answers": reply}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            pass

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="claude-code", choices=BACKENDS)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    for v in VERSIONS:
        retriever(v)  # build both indexes before the first question
    print(f"Docs assistant ({a.backend}, {a.model}) at http://localhost:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(a.backend, a.model)).serve_forever()


if __name__ == "__main__":
    main()
