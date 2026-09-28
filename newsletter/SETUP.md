# FedReg Intel email list

Status: drafts prepared; subscriber service not connected; no automatic mail enabled.

## Website signup copy

**Join the FedReg Intel monthly brief**

The month’s videos, practical rulemaking guidance, and news about books by Jarrett Paul Dudley — delivered to your inbox.

Email address (required); first name (optional).

Consent: “Send me FedReg Intel’s monthly updates and book promotions. I can unsubscribe at any time.”

Button: **Join the email list**

After submission: “Check your inbox for a confirmation link. You’ll join the list after confirming your email address.”

## Sending setup

- Use a provider-hosted double-opt-in form; do not store subscriber addresses in this public repository.
- Authenticate a sender on fedregintel.com using the selected provider’s DKIM instructions. Preserve existing Cloudflare routing MX records and do not create a second SPF record.
- Send welcome.html once, only after confirmation. Reply-to: hello@fedregintel.com.
- Send one monthly roundup for the preceding calendar month, using America/New_York dates, on the first of each month at 10 AM Eastern.
- Recipients: confirmed subscribers only, excluding all unsubscribed, bounced, and suppressed contacts.
- Substitute the provider’s unsubscribe merge tag and the owner-supplied public mailing address before activating either email. Include both HTML and plain text.
- Regenerate drafts from current data/videos.json. Never send a stale archive without investigating refresh failures. Use a per-month campaign ID and check its sent status before retrying to avoid duplicate campaigns.
- Verify signup, confirmation, welcome delivery, unsubscribe suppression, and a test monthly send before enabling production delivery.

## Draft generation

`python scripts/build_newsletter.py --month 2026-09 --output newsletter/drafts`

September 2026 drafts are previews of the month so far until September ends. The script does not send mail. Templates retain conspicuous placeholders until an email provider is configured.

The current catalog promotes only the verified published book: https://www.amazon.com/dp/B0HL97PYTB. Add additional books only when their publication and purchase links are confirmed.
