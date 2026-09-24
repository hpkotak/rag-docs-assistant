---
title: "API: authentication"
updated: 2026-01-12
---
# API: authentication

The Tallyfox API is available on the Growth and Scale plans. The base URL is
`https://api.tallyfox.example/v2`.

## API keys

Owners and Admins can create API keys in **Settings > Developers**. Send the key in the
`Authorization` header as a bearer token:

```
Authorization: Bearer tfx_live_...
```

Live keys start with `tfx_live_` and act on your real data. Test keys start with `tfx_test_` and act on
a separate test copy of your account, where no real emails are sent and no money moves.

A key has the permissions of the person who created it. If that person is removed from the team, their
keys stop working.

## Rotating keys

Create a new key, update your code, then delete the old key. Deleted keys stop working immediately.
