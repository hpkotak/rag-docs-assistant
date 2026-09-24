---
title: "API: error codes"
updated: 2026-01-12
---
# API: error codes

Errors return a JSON body with a `code` and a `message`.

| Code | HTTP status | Meaning | What to do |
| --- | --- | --- | --- |
| `E1001` | 401 | The API key is missing, wrong or deleted | Check the `Authorization` header |
| `E1002` | 403 | The key's owner doesn't have permission for this action | Use a key created by an Owner or Admin |
| `E2004` | 409 | The invoice already has a payment recorded, so it's locked | Issue a credit note instead of editing |
| `E2010` | 422 | The invoice number has already been used | Leave the number out and let Tallyfox assign one |
| `E3001` | 422 | The invoice currency isn't enabled for your account | Invoicing in other currencies needs Growth or Scale |
| `E4290` | 429 | Too many requests | Wait for the number of seconds in `Retry-After` |
