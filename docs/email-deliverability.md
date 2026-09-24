---
title: "Troubleshooting: clients not receiving invoices"
updated: 2026-02-18
---
# Troubleshooting: clients not receiving invoices

Invoice emails are sent from `invoices@tallyfox.example`, with your email address as the reply-to.

## Check the invoice timeline

Open the invoice and look at its timeline. It shows when the email was delivered and opened. If the
email bounced, the timeline shows the reason, such as a mistyped address or a full mailbox.

## If emails land in spam

- Ask your client to add `invoices@tallyfox.example` to their contacts or safe senders.
- On Growth and Scale, send from your own domain instead. Go to **Settings > Email** and add the SPF
  and DKIM records we show you to your domain's DNS. Sending starts once both records are verified,
  which can take up to 48 hours.

## Sending the link another way

Every invoice has a **Copy link** button, so you can send the client portal link by text message or chat.
