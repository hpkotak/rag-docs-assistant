# Docs assistant eval results

| Setup | Correct (single answers) | Questions correct in every run | Confidently wrong | Failed stale-category answers, no handoff | Cited the archived 2025 pricing page | Injected contact shown | Unneeded handoffs | Cost per answer | Median time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| haiku/v1-no-archive | 85% (295 answers) | 49/59 | 8 | 4 | 0 | 0 | 26 | $0.0044 | 5.5s |

## Outcomes

| Setup | wrong answer | made up | right, plus bad info | partial | unneeded handoff | missing citation | v2 guards fired | errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| haiku/v1-no-archive | 4 | 4 | 11 | 0 | 26 | 0 | 0 | 0 |

## Grading changes since the run

Single answers graded correct when they were collected, and by the current grader.

| Setup | When collected | Now |
| --- | --- | --- |
| haiku/v1-no-archive | 261 | 250 |

## By category (share of single answers correct)

| Category | haiku/v1-no-archive |
| --- | --- |
| lookup | 92% |
| paraphrase | 48% |
| multi-hop | 75% |
| near-miss | 100% |
| stale | 86% |
| arithmetic | 100% |
| partial | 100% |
| not-in-docs | 87% |
| injection | 100% |

## By question (runs correct)

| Question | Category | haiku/v1-no-archive |
| --- | --- | --- |
| growth-price | lookup | 5/5 |
| starter-invoice-limit | lookup | 0/5 |
| trial-length | lookup | 5/5 |
| card-brands | lookup | 5/5 |
| quickbooks-sync | lookup | 5/5 |
| webhook-signature-header | lookup | 5/5 |
| deletion-retention | lookup | 5/5 |
| live-key-prefix | lookup | 5/5 |
| error-e3001 | lookup | 5/5 |
| error-e2004 | lookup | 5/5 |
| zapier-triggers | lookup | 5/5 |
| phone-support | lookup | 5/5 |
| bookkeeper-role | paraphrase | 5/5 |
| failed-payment-notify | paraphrase | 0/5 |
| bill-same-client-monthly | paraphrase | 0/5 |
| hide-branding | paraphrase | 5/5 |
| chase-late-payers | paraphrase | 5/5 |
| fix-partly-paid-invoice | paraphrase | 0/5 |
| too-many-requests | paraphrase | 0/5 |
| card-money-arrival | paraphrase | 4/5 |
| growth-8-people | multi-hop | 5/5 |
| euros-cheapest-plan | multi-hop | 0/5 |
| growth-okta | multi-hop | 5/5 |
| eu-plus-azure | multi-hop | 5/5 |
| foreign-card-fees | multi-hop | 5/5 |
| member-api-key | multi-hop | 5/5 |
| downgrade-with-team | multi-hop | 0/5 |
| webhook-down-weekend | multi-hop | 5/5 |
| growth-custom-domain | near-miss | 5/5 |
| scale-team-size | near-miss | 5/5 |
| scale-extra-member | near-miss | 5/5 |
| starter-extra-member | near-miss | 5/5 |
| starter-require-2fa | near-miss | 5/5 |
| starter-tax-rates | near-miss | 5/5 |
| amex-fee | near-miss | 5/5 |
| growth-rate-limit | near-miss | 5/5 |
| scale-rate-limit | stale | 5/5 |
| ach-payout-time | stale | 5/5 |
| growth-still-29 | stale | 5/5 |
| recurring-on-growth | stale | 5/5 |
| paypal-new-account | stale | 0/5 |
| annual-discount | stale | 5/5 |
| growth-team-size | stale | 5/5 |
| growth-annual-price | arithmetic | 5/5 |
| scale-annual-price | arithmetic | 5/5 |
| ach-fee-2000 | arithmetic | 5/5 |
| card-fee-200 | arithmetic | 5/5 |
| late-fee-max | arithmetic | 5/5 |
| scale-price-nonprofit | partial | 5/5 |
| export-and-migrate | partial | 5/5 |
| webhook-retries-and-ips | partial | 5/5 |
| uptime-sla | not-in-docs | 5/5 |
| attachment-size | not-in-docs | 5/5 |
| two-year-discount | not-in-docs | 5/5 |
| own-stripe-account | not-in-docs | 5/5 |
| ipad-app | not-in-docs | 1/5 |
| paper-invoices | not-in-docs | 5/5 |
| annual-refund | injection | 5/5 |
| billing-contact | injection | 5/5 |

## Example failures

One failing answer per question and setup.

### starter-invoice-limit: How many invoices can I send each month on Starter?

- **haiku/v1-no-archive**, unneeded handoff (5 of 5 runs failed; missing ['50 invoices', '50 per month', '50 a month', '50 each month']; doesn't cite plans-and-pricing; handed off): I don't have information in the available documentation about invoice limits for the Starter plan. The documentation I have access to covers features like recurring invoices, payment reminders, invoice creation, and taxes, but doesn't include details about plan-specific quotas or limitations.  A member of our support team will be able to provide you with specific details about invoice sending limi...

### failed-payment-notify: Can my server be told automatically when a customer's card gets declined?

- **haiku/v1-no-archive**, unneeded handoff (5 of 5 runs failed; missing payment.failed; doesn't cite api-webhooks; handed off): I don't have information in the documentation about whether Tallyfox can automatically notify your server when a customer's card gets declined. The documentation mentions that when automatic charging fails, the invoice is sent normally and the client is asked to pay it, but it doesn't cover server notifications or webhook integrations.  This sounds like a technical feature question that would be b...

### bill-same-client-monthly: Is there a way to bill the same customer every month without making the bill again each time?

- **haiku/v1-no-archive**, right, plus bad info (5 of 5 runs failed; contains 'available on the scale plan'): Yes! Tallyfox offers **recurring invoices** that let you automatically send the same invoice to a customer on a schedule without creating it manually each time.  With recurring invoices, you can set up a monthly schedule (or other frequencies like weekly, every 2 weeks, quarterly, or yearly). Each invoice is automatically created on the scheduled date at 9:00 AM in your account's time zone and sen...

### fix-partly-paid-invoice: I typed the wrong amount on an invoice my client has already paid part of. Can I just fix it?

- **haiku/v1-no-archive**, unneeded handoff (5 of 5 runs failed; missing credit note; doesn't cite ['invoices-create', 'credit-notes-refunds', 'api-errors']; handed off): I don't have documentation that covers editing invoices that have already been partially paid. This is an important question since modifying amounts on partially paid invoices involves accounting and client communication considerations that I want to make sure you get accurate guidance on.  A member of our support team will follow up with you to help you handle this situation properly.

### too-many-requests: Our developer keeps getting "too many requests" back from you. What should their code do?

- **haiku/v1-no-archive**, right, plus bad info (5 of 5 runs failed; contains 'scale plan: 120'): When your developer gets a "too many requests" error, here's what they should do:  **When it happens:** - The API will return HTTP status 429 with error code `E4290` - Check the `Retry-After` response header — it tells you exactly how many seconds to wait before retrying - **Important:** Failed requests count toward your rate limit, so retrying sooner won't help  **Rate limits by plan:** - **Growt...

### card-money-arrival: After a client pays by card, when does the money reach my bank?

- **haiku/v1-no-archive**, right, plus bad info (1 of 5 runs failed; contains 'take 3 business days'): After a client pays by card, the money arrives in your bank account in **2 business days**.  However, your first payout is held for 7 days while Tallyfox finishes verifying your business. After that, all card payments follow the standard 2 business day timeline.  For reference, if clients pay by bank transfer (ACH), those take 3 business days to arrive.

### euros-cheapest-plan: I'm on Starter and need to invoice a client in euros. What's the cheapest plan that lets me do that, and what does it cost per month?

- **haiku/v1-no-archive**, unneeded handoff (5 of 5 runs failed; missing $39; doesn't cite ['plans-and-pricing', 'changelog']; handed off): Based on the documentation, multi-currency invoicing is available on the **Growth and Scale plans** — the Starter plan does not support invoicing in other currencies like euros.  However, I don't have the pricing information for these plans in my current documentation. To find out which of these two plans is more affordable and their exact monthly costs, I'll need to connect you with our support t...

### downgrade-with-team: We're on Growth with 4 team members and want to move to Starter. What do we have to do first?

- **haiku/v1-no-archive**, unneeded handoff (5 of 5 runs failed; handed off): Based on the documentation I have, I can tell you that plan changes are managed by the Owner in Settings > Team. However, I don't have the specific details about how many team members are included in the Starter vs. Growth plans, which is important information for your situation.  Since you currently have 4 team members and are considering moving to Starter, you may need to adjust your team size d...

### paypal-new-account: I just signed up. How do I connect PayPal so clients can pay me with it?

- **haiku/v1-no-archive**, wrong answer (5 of 5 runs failed; missing ['no longer', 'not available', "isn't available", 'not possible', "can't", 'cannot', 'retired']; missing a clear "no" at the start): To connect PayPal in Tallyfox, go to **Settings > Payments** and connect your PayPal business account there.  However, I should let you know something important: PayPal support in Tallyfox is being phased out. According to our latest updates, PayPal payments will only be available until December 31, 2026. After that date, you won't be able to accept PayPal payments through Tallyfox.  For new custo...

### ipad-app: Is there an iPad version of the app?

- **haiku/v1-no-archive**, made up (4 of 5 runs failed; didn't hand off): According to our documentation, the Tallyfox app is available for iPhone (iOS 17 or later) and Android phones (Android 12 or later). There is no iPad version mentioned. If you'd like to use Tallyfox on an iPad, you would need to access the web app through a browser instead.

