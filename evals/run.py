"""Run the eval set: every question x version x model, repeated --trials times.

    uv run python -m evals.run                                    # offline mock model, a few seconds
    uv run python -m evals.run --backend claude-code --models haiku,opus --trials 5

Results are appended to <out>/results.jsonl as each answer comes back, so an interrupted run
continues where it stopped when started again with the same --out.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from assistant.backends import BACKENDS, ModelError, UsageLimit, redact
from assistant.corpus import ROOT
from assistant.pipeline import VERSIONS, answer, retrieve
from evals import report
from evals.grade import grade

QUESTIONS = yaml.safe_load((ROOT / "evals" / "questions.yaml").read_text())


def run_one(backend: str, model: str, version: str, q: dict, chunks, attempts: int = 3) -> dict:
    for attempt in range(1, attempts + 1):
        try:
            out = answer(q["q"], version, backend, model, chunks)
            break
        except (ModelError, subprocess.TimeoutExpired, OSError) as e:
            if attempt == attempts:
                return {"error": redact(str(e))}
            time.sleep(30 * attempt)  # usually a rate limit
    out["answer"] = redact(out["answer"])
    return {**out, **grade(q, out)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="mock", choices=BACKENDS)
    ap.add_argument("--models", default="haiku", help="comma-separated Claude model aliases (ignored by mock)")
    ap.add_argument("--versions", default="v1,v2")
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--only", default="", help="comma-separated question ids")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    models = ["mock"] if a.backend == "mock" else a.models.split(",")
    versions = a.versions.split(",")
    questions = [q for q in QUESTIONS if not a.only or q["id"] in a.only.split(",")]
    out = Path(a.out or ROOT / "results" / a.backend)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "results.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if "error" not in r:
                done.add((r["model"], r["version"], r["question"], r["trial"]))

    # Retrieval doesn't depend on the model or the trial, so do it once per question, up front.
    sources = {(v, q["id"]): retrieve(q["q"], v) for v in versions for q in questions}
    jobs = [(m, v, q, t) for m in models for v in versions for q in questions
            for t in range(1, a.trials + 1) if (m, v, q["id"], t) not in done]
    print(f"{len(jobs)} answers to get ({len(done)} already done) -> {path}", flush=True)
    lock = threading.Lock()
    with ThreadPoolExecutor(a.workers) as pool, path.open("a") as f:
        futures = {pool.submit(run_one, a.backend, m, v, q, sources[(v, q["id"])]): (m, v, q, t)
                   for m, v, q, t in jobs}
        for n, fut in enumerate(as_completed(futures), 1):
            m, v, q, t = futures[fut]
            try:
                result = fut.result()
            except UsageLimit as e:
                print(f"Stopping: {e}. Run the same command again after it resets to continue.", flush=True)
                for other in futures:
                    other.cancel()
                break
            row = {"model": m, "version": v, "question": q["id"], "category": q["category"], "trial": t, **result}
            with lock:
                f.write(json.dumps(row) + "\n")
                f.flush()
            status = "ERROR" if "error" in row else ("pass" if row["pass"] else row["outcome"].upper())
            print(f"[{n}/{len(jobs)}] {m} {v} {q['id']} #{t}: {status}", flush=True)

    report.write(out)
    sys.stdout.flush()
    os._exit(0)  # onnxruntime can crash while Python shuts down; everything is saved by now


if __name__ == "__main__":
    main()
