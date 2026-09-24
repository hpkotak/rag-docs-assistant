---
title: "API: rate limits"
updated: 2026-01-12
---
# API: rate limits

Each account can make a limited number of API requests per minute:

| Plan | Requests per minute |
| --- | --- |
| Growth | 60 |
| Scale | 120 |

Requests made with test keys have their own, separate limit of 30 requests per minute.

## When you hit the limit

The API returns HTTP status 429 with error code `E4290`. The `Retry-After` header tells you how many
seconds to wait before trying again. Retrying sooner doesn't help, because failed requests count
towards the limit too.

To stay under the limit, use the list endpoints with `limit=100` instead of fetching records one by one.
