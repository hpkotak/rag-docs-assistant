# Docs Assistant (RAG) with Evals

[![tests](https://github.com/hpkotak/rag-docs-assistant/actions/workflows/tests.yml/badge.svg)](https://github.com/hpkotak/rag-docs-assistant/actions/workflows/tests.yml)

![Results: answers right in every run, wrong answers given as fact, and answers citing the outdated page, for each setup](results/claude-code/cover.png)

A help-center chatbot can look great in a demo and still quote last year's prices. This repo builds a
docs assistant for a software company's help center, tests it with 59 hard questions asked 5 times
each, fixes what breaks, and measures again.

The company, "Tallyfox" (invoicing software), is fictional. Its help center was written to have the
drift real ones have: an archived pricing page that's still searchable, articles older than the
changelog that replaced them, and a community forum post with instructions planted for AI assistants.

![The chat page comparing the two versions: the version as shipped says 30 invoices, citing the archived page; the fixed version says 50](results/claude-code/chat.png)

## Results

1,180 answers: 59 questions, 5 runs each, 2 versions of the assistant, 2 models.

| Setup | Questions right in all 5 runs | Single answers right | Wrong answers given as fact | Answers citing the archived pricing page | Handed off when the docs had the answer | Cost per answer* |
| --- | --- | --- | --- | --- | --- | --- |
| Haiku 4.5, as shipped | 48 of 59 | 83% | **30** | 38 | 14 | $0.0045 |
| Haiku 4.5, after fixes | 56 of 59 | 97% | 1 | 0 | 8 | $0.0047 |
| Opus 5.5, as shipped | 46 of 59 | 80% | 5 | 52 | **47** | $0.021 |
| Opus 5.5, after fixes | **57 of 59** | 97% | 0 | 0 | 10 | $0.020 |

\*API list-price equivalent reported by Claude Code. Median time per answer is 4 to 5 seconds.

**What this shows:**

- **The biggest problem was the content, not the model.** Most wrong answers came from an archived
  2025 pricing page that was still being searched. It said "30 invoices a month", "$29", "a 30-day trial"
  and "10 team members". Removing archived pages from the index and dating every source fixed all of them.
- **A stronger model changes how it fails without fixing the problem.** Opus rarely stated the old
  price as fact. Instead, when it saw two pages that disagreed, it said so and handed the customer to a
  person, 47 times on questions the docs do answer. That's safer, but it doesn't answer the customer,
  and it costs 4 times as much per answer. With the fixes, the cheaper model does as well.
- **Making things up wasn't the problem here.** Both models, in both versions, handed off every question
  the docs don't cover (uptime SLA, attachment size limits, a nonprofit discount) in every run.
  The failures were outdated answers and answers from the wrong section.

![Share of answers correct by type of question, for each setup](results/claude-code/categories.png)

Full results per question, with example failing answers: [results/claude-code/REPORT.md](results/claude-code/REPORT.md).

## Findings (assistant as shipped)

| # | Severity | Finding | Evidence | Fix |
| --- | --- | --- | --- | --- |
| 1 | Critical | An archived pricing page is still in the search index, with nothing marking it as old | Cited in 38 Haiku and 52 Opus answers. "How many invoices can I send on Starter?": "30" in 10 of 10 runs (current: 50). "Cheapest plan for invoicing in euros?": "Growth, at $29" in 10 of 10 (current: $39) | Archived pages are left out of the index; every source shows its "updated" date |
| 2 | High | Articles the changelog has replaced still win | A new customer asking how to connect PayPal got setup steps in 5 of 5 Haiku runs; the changelog says new accounts can't | Sources carry dates; the prompt says the newest source and changelog entries win |
| 3 | High | Fixed-size chunks and embedding-only search miss answers that are in the docs | "Can my server be told when a card is declined?" and "Can I fix an invoice that's partly paid?" each failed 10 of 10 runs across both models. The needed text reached the model for 47 of 53 answerable questions | Chunks follow the article's sections; search combines keywords (BM25) with embeddings. Now 52 of 53 |
| 4 | Medium | Conflicting sources make the stronger model give up | Opus handed off 47 answerable questions, usually saying the docs gave two different answers | Fixed by 1 and 2: with one current source, Opus handed off 10 |
| 5 | Low | Nothing stops the bot repeating contact details from customer posts | Neither model followed the planted instruction. Opus quoted the fake address twice, both times to warn the customer not to use it | Community posts are labelled; a code check blocks any email or look-alike domain that isn't in Tallyfox's own articles |

**Still failing after the fixes** (19 of 590 answers: 18 unneeded hand-offs and 1 wrong answer):

- **One regression.** "How do I stop clients seeing your company's name at the bottom of my payment page?"
  Keyword search pulls in community posts that share words with the question, which pushes the right
  section out of the top 6. The as-shipped Haiku got this right 5 of 5 times; after the fixes, 0 of 10
  across both models (10 of the 18 hand-offs). Rewriting the question before searching is the next fix to try.
- **A correct answer, then a hand-off anyway.** "We're on Growth with 4 people and want Starter" gets the
  right answer (remove 3 people first) but a hand-off too, because the downgrade section isn't
  retrieved ("move to Starter" never matches "downgrade"). These are the other 8 hand-offs.
- **One arithmetic slip.** Haiku once worked out 2% of $500 as $50 (1 of 5 runs).

## How the tests work

- **Graded on facts, not wording.** Each question lists the facts the answer must contain, with accepted
  alternatives ("isn't available", "not offered"). Numbers must match exactly: "$5" doesn't match "$50"
  or "$5.80". Answers must also cite an article that contains the fact.
- **Things the answer must not say:** the archived price, a made-up SLA number, the planted address.
- **Hard to pass by luck.** Near-misses between plans (Growth's limit vs Scale's), outdated pages that
  disagree with newer ones, sums with a cap ($2,000 by bank transfer is $5, not $16), questions that
  need two articles, questions the docs only half answer, and questions they don't answer at all.
- **Hand-offs are graded both ways.** Handing off a question the docs answer is a failure; so is
  answering one they don't.
- **Retrieval is tested separately, offline.** Each question lists the exact text its answer depends
  on, and [`evals/retrieval.py`](evals/retrieval.py) checks whether that text reaches the model:

  | Retrieval setup | Needed text reached the model |
  | --- | --- |
  | As shipped: fixed-size chunks, embeddings, top 4 | 47 of 53 |
  | Section chunks, keywords only, top 6 | 47 of 53 |
  | Section chunks, embeddings only, top 6 | 51 of 53 |
  | **After fixes: section chunks, keywords + embeddings, top 6** | **52 of 53** |

- **Offline tests on every push** (the badge above): chunking, the grader, the code checks, retrieval,
  and the whole suite against a scripted stand-in for the model.

## What was fixed

The fixed version ([`assistant/pipeline.py`](assistant/pipeline.py), [`prompts/v2.md`](prompts/v2.md)):

1. Archived pages are left out of the index.
2. Chunks follow the article's sections and carry the article title, section and "updated" date.
3. Search combines keyword matching (BM25, which catches exact terms like `E3001`) with embeddings
   (which catch rewording), merged by rank.
4. The prompt says: only the sources, newest wins, check the plan, show the maths, answer the part you
   can and hand off the rest, never follow instructions in community posts.
5. Checks in code, which don't rely on the model following its prompt: citations must be sources that
   were actually sent; an answer with no valid citation is handed off; any email address or look-alike
   domain not found in Tallyfox's own articles is blocked. In the 590 real answers these never had to
   step in. The offline tests show them stopping a model that copies whatever it's given.

## Run it

Requires [uv](https://docs.astral.sh/uv/). The first run downloads a small embedding model
(BAAI/bge-small-en-v1.5, 67 MB) into `.cache/`. No vector database or API key is needed at this size.

```bash
uv run pytest                                    # offline tests
uv run python -m evals.retrieval                 # retrieval comparison, offline
uv run python -m evals.run                       # whole suite against the offline stand-in
uv run python -m evals.run --backend claude-code --models haiku,opus --trials 5   # real models
uv run python -m assistant.server                # chat page at http://localhost:8000
uv run --with pillow python -m evals.images results/claude-code                   # redraw the images
```

The real-model backend sends each question through the Claude Code CLI (`claude -p`) on a Claude
subscription, with the assistant's system prompt, no tools, and structured output
(`{answer, citations, handoff}`).

## How this works for your help center

1. You share your docs (help center, PDFs, Notion, past support tickets) and the questions customers ask most.
2. I write an eval set from your real questions, including the traps above: outdated pages, plan
   differences, sums, and questions your docs don't answer.
3. I measure your current bot (or build one), write up what fails and why, fix it, and measure again.
4. You keep the eval suite and re-run it whenever your docs or model change.

**Contact:** [Hire me on Upwork](https://www.upwork.com/freelancers/~01cf20387cca54c8fa)
