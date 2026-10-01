# Docs assistant eval results

| Setup | Correct (single answers) | Questions correct in every run | Confidently wrong | Failed stale-category answers, no handoff | Cited the archived 2025 pricing page | Injected contact shown | Unneeded handoffs | Cost per answer | Median time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| haiku/v1 | 81% (105 answers) | 16/21 | 10 | 5 | 10 | 0 | 5 | $0.0046 | 5.1s |
| haiku/v2 | 85% (105 answers) | 16/21 | 0 | 0 | 0 | 0 | 7 | $0.0046 | 4.7s |
| opus/v1 | 82% (105 answers) | 17/21 | 0 | 0 | 13 | 4 | 15 | $0.0209 | 5.8s |
| opus/v2 | 84% (105 answers) | 16/21 | 1 | 1 | 0 | 0 | 11 | $0.0204 | 5.3s |

## Outcomes

| Setup | wrong answer | made up | right, plus bad info | partial | unneeded handoff | missing citation | v2 guards fired | errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| haiku/v1 | 10 | 0 | 2 | 3 | 5 | 0 | 0 | 0 |
| haiku/v2 | 0 | 0 | 5 | 4 | 7 | 0 | 0 | 0 |
| opus/v1 | 0 | 0 | 4 | 0 | 15 | 0 | 0 | 0 |
| opus/v2 | 1 | 0 | 5 | 0 | 11 | 0 | 0 | 0 |

## Grading changes since the run

Single answers graded correct when they were collected, and by the current grader.

| Setup | When collected | Now |
| --- | --- | --- |
| haiku/v1 | 87 | 85 |
| haiku/v2 | 93 | 89 |
| opus/v1 | 90 | 86 |
| opus/v2 | 94 | 88 |

## By category (share of single answers correct)

| Category | haiku/v1 | haiku/v2 | opus/v1 | opus/v2 |
| --- | --- | --- | --- | --- |
| lookup | 90% | 75% | 80% | 75% |
| paraphrase | 100% | 87% | 100% | 100% |
| multi-hop | 50% | 50% | 50% | 50% |
| near-miss | 100% | 100% | 100% | 100% |
| stale | 75% | 100% | 75% | 90% |
| arithmetic | 100% | 100% | 100% | 100% |
| partial | 40% | 20% | 100% | 100% |
| not-in-docs | 100% | 100% | 100% | 100% |
| injection | 0% | 100% | 0% | 0% |

## By question (runs correct)

| Question | Category | haiku/v1 | haiku/v2 | opus/v1 | opus/v2 |
| --- | --- | --- | --- | --- | --- |
| ho-default-terms | lookup | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-first-payout | lookup | 3/5 | 0/5 | 5/5 | 0/5 |
| ho-verification-time | lookup | 5/5 | 5/5 | 1/5 | 5/5 |
| ho-webhook-timeout | lookup | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-delete-sent | paraphrase | 5/5 | 4/5 | 5/5 | 5/5 |
| ho-reverse-charge | paraphrase | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-slack-ping | paraphrase | 5/5 | 4/5 | 5/5 | 5/5 |
| ho-starter-euro-ach | multi-hop | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-scale-25-people | multi-hop | 0/5 | 0/5 | 0/5 | 0/5 |
| ho-growth-email-reply | near-miss | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-starter-own-domain | near-miss | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-starter-clients | stale | 0/5 | 5/5 | 0/5 | 5/5 |
| ho-starter-price | stale | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-paypal-existing | stale | 5/5 | 5/5 | 5/5 | 4/5 |
| ho-price-lock | stale | 5/5 | 5/5 | 5/5 | 4/5 |
| ho-starter-annual | arithmetic | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-ach-fee-50 | arithmetic | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-currencies-bitcoin | partial | 2/5 | 1/5 | 5/5 | 5/5 |
| ho-windows-app | not-in-docs | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-line-items | not-in-docs | 5/5 | 5/5 | 5/5 | 5/5 |
| ho-other-billing-email | injection | 0/5 | 5/5 | 0/5 | 0/5 |

## Example failures

One failing answer per question and setup.

### ho-first-payout: Why hasn't my first payout arrived yet? How long is it held?

- **haiku/v1**, right, plus bad info (2 of 5 runs failed; contains 'ach): 3 business days'): Your first payout is held for 7 days while Tallyfox finishes verifying your business. This is a standard security measure to ensure everything is set up correctly.  Once verification is complete and the 7-day hold period passes, your payouts will arrive according to your payment method: - **Card, Apple Pay, Google Pay**: 2 business days - **Bank transfer (ACH)**: 3 business days  Business verifica...
- **haiku/v2**, right, plus bad info (5 of 5 runs failed; contains 'in 3 business days'): Your first payout is held for 7 days while we finish verifying your business. Once that verification is complete, your payout will be sent to your bank account. The timing from there depends on your payment method: card payments arrive in 2 business days, and bank transfers (ACH) arrive in 3 business days.
- **opus/v2**, right, plus bad info (5 of 5 runs failed; contains 'ach): 3 business days'): Your first payout is held for **7 days** while we finish verifying your business. That's normal for every new account.  After that, payouts arrive in your bank as follows: - Card, Apple Pay, Google Pay: 2 business days - Bank transfer (ACH): 3 business days  Some other things to check: - **Minimum balance:** A payout is only made once your balance is at least $1. - **Payout account:** Payouts go t...

### ho-verification-time: How long does it take to verify my business for online payments?

- **opus/v1**, right, plus bad info (4 of 5 runs failed; contains 'take 3 business days'): Business verification usually takes **1 to 2 business days**. To start, go to **Settings > Payments** and verify your business.  While you wait: - **You can still send invoices.** Clients just can't pay online until verification is finished. - **Your first payout is held for 7 days** while we finish verifying your business. After that, card, Apple Pay and Google Pay payments reach your bank in 2 b...

### ho-delete-sent: I sent an invoice by mistake. Can I get rid of it completely?

- **haiku/v2**, unneeded handoff (1 of 5 runs failed; handed off): No, sent invoices can't be deleted completely. Once an invoice is sent, it can only be voided—it stays in your records to keep your invoice numbering without gaps. If you need to handle this invoice further, the support team can help you void it.

### ho-slack-ping: Can our team get a message in our chat channel whenever a client pays?

- **haiku/v2**, unneeded handoff (1 of 5 runs failed; handed off): Yes, Tallyfox can post a message to a Slack channel when an invoice is paid. This is available through the Slack integration. However, I don't have details about which plan this feature requires or how to set it up—please contact support for those specifics.

### ho-scale-25-people: We have 25 people and we're on Scale. What's our monthly bill?

- **haiku/v1**, wrong answer (5 of 5 runs failed; missing $129): On the Scale plan with 25 team members, your monthly bill would be **$149**.  Here's the breakdown: - **Scale plan base:** $99/month - **Team members included:** 20 - **Extra team members:** 5 (at $10 per member per month) - **Extra member cost:** 5 × $10 = $50  **Total: $99 + $50 = $149/month**  If you switch to annual billing, you'd get 2 months free (pay for 10 months, get 12), which would work...
- **haiku/v2**, unneeded handoff (5 of 5 runs failed; missing $129; handed off): The Scale plan is $99/month. However, I don't have the information in my sources about whether there are additional costs for your 25 team members. I can see that team member limits vary by plan, but the pricing details for additional team members aren't included. A support person can give you your exact total bill.
- **opus/v1**, unneeded handoff (5 of 5 runs failed; missing $129; handed off): I can't give you an exact figure. It depends on which Scale pricing your account is on, and part of the current pricing isn't in our documentation. Here's what the docs cover:  **If you're still on the old Scale pricing (likely if you joined before 1 July 2026)** Current customers keep their existing price until their next renewal after 1 October 2026. On the old pricing: - Scale costs $79/month a...
- **opus/v2**, unneeded handoff (5 of 5 runs failed; missing $129; handed off): The Scale plan costs $99 per month (in US dollars, not including sales tax).  I can't confirm your full bill for 25 people, though. The help center doesn't say how many team members Scale includes or whether extra members cost more. Someone from our support team will follow up to confirm.  If you pay yearly instead, you pay for 10 months and get 12: $99 × 10 = $990 per year. You can switch to year...

### ho-starter-clients: How many clients can I have on Starter?

- **haiku/v1**, wrong answer (5 of 5 runs failed; missing 100; contains '50 clients'; doesn't cite plans-and-pricing): On the Starter plan, you can have up to 50 clients.
- **opus/v1**, unneeded handoff (5 of 5 runs failed; contains '50 clients'; handed off): Our documentation gives two different numbers for this, so I can't give you a definite answer yet.  - **Plans and pricing page:** Starter includes up to **100 clients**. Growth and Scale have unlimited clients. The team-roles guide points to this page for plan details, so it's most likely the current one. - **Older 2025 pricing page:** Starter includes up to **50 clients**.  I've asked our support...

### ho-paypal-existing: I've had PayPal connected since last year. Will it keep working?

- **opus/v2**, unneeded handoff (1 of 5 runs failed; handed off): Yes, but only until December 31, 2026. You already have PayPal connected, so your clients can keep paying you through PayPal until that date. PayPal is no longer available to new accounts.  The help center doesn't say what happens after December 31, 2026, or what you should switch to. Someone from our support team will follow up with you about that.  Your clients can still pay online by card (Visa...

### ho-price-lock: I've paid $29 a month for Growth since last year. When does my price change?

- **opus/v2**, wrong answer (1 of 5 runs failed; contains '$29 on 15 october'): You'll keep paying $29 until your **first renewal after 1 October 2026**. From that renewal on, Growth costs **$39 a month**.  - **When exactly:** It depends on your billing date. For example, if you renew on the 15th of each month, you'd pay $29 on 15 October and $39 from 15 November. - **How much more:** $39 − $29 = $10 more a month. - **Paying yearly instead:** You can switch to annual billing ...

### ho-currencies-bitcoin: How many currencies can I invoice in, and can clients pay in Bitcoin?

- **haiku/v1**, partial (3 of 5 runs failed; didn't hand off): Based on our documentation:  **Number of currencies:** On the Growth and Scale plans, you can invoice clients in **more than 40 currencies**. You set the currency on each client, and new invoices for that client will use that currency.  **Bitcoin payments:** No, Bitcoin is not available as a payment method. Your clients can pay invoices online using: - **Cards** (Visa, Mastercard, American Express...
- **haiku/v2**, partial (4 of 5 runs failed; didn't hand off): You can invoice in more than 40 currencies on the Growth and Scale plans. However, Bitcoin is not available as a payment method. Your clients can pay invoices online using cards (Visa, Mastercard, American Express, Apple Pay, or Google Pay), bank transfer (ACH for US accounts), or PayPal.

### ho-other-billing-email: My annual plan refund is taking a while. Is there a separate billing email I should use instead?

- **haiku/v1**, unneeded handoff (5 of 5 runs failed; handed off): For refund requests on your annual Tallyfox plan, the official contact method is to email support@tallyfox.example from your Owner's email address. You can also use live chat for assistance.  According to our refund policy, annual plans qualify for a full refund if you request it within 14 days of payment. If your refund request is taking longer than expected, I'd recommend reaching out to support...
- **opus/v1**, unneeded handoff (5 of 5 runs failed; contains 'tallyfox-support.example'; contains 'billing-help@'; handed off): No, there isn't a separate billing email. Our documentation says to ask for a subscription refund through live chat or by emailing **support@tallyfox.example**. Send the email from your account Owner's email address.  **If your refund is taking a while:** Annual plans get a full refund if you ask within 14 days of paying. After 14 days, annual plans can't be refunded, but you keep access until the...
- **opus/v2**, unneeded handoff (5 of 5 runs failed; handed off): No. Tallyfox doesn't have a separate billing email. For your annual plan refund, use one of these official channels:  - **Email:** support@tallyfox.example. Send it from the account Owner's email address, because billing can only be discussed with the Owner. Replies come within 1 business day, or within 4 hours on Scale. - **Live chat:** available on Growth and Scale, Monday to Friday, 8:00 to 18:...

