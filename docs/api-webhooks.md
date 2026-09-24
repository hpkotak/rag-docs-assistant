---
title: "API: webhooks"
updated: 2026-01-12
---
# API: webhooks

Webhooks tell your server when something happens in Tallyfox. Add an endpoint URL in
**Settings > Developers > Webhooks** and choose the events to receive.

## Events

| Event | Sent when |
| --- | --- |
| `invoice.sent` | An invoice is sent to a client |
| `invoice.paid` | An invoice is paid in full |
| `invoice.overdue` | An invoice passes its due date unpaid |
| `payment.failed` | A client's online payment fails |
| `payout.paid` | A payout is sent to your bank |

## Verifying webhooks

Every webhook has a `Tallyfox-Signature` header: an HMAC-SHA256 of the request body, signed with your
endpoint's signing secret. Reject requests where the signature doesn't match.

## Responding and retries

Your endpoint must return a 2xx status within 10 seconds. Otherwise we retry up to 8 times over 3 days,
waiting longer between each attempt. If every attempt fails for 3 days, the endpoint is turned off and
Owners and Admins get an email. Events that failed can be resent from the webhook's log for up to 30 days.
