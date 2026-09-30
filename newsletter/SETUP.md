# Signup collection — sending remains off

The website collects explicit consent for future FedReg Intel updates and book promotions.
Cloudflare Worker: fedregintel-signups (workers.dev endpoint in signup-section.html).
Private D1 database: fedregintel-subscribers. Subscriber records must never be exported to this public repository.
Cloudflare Dashboard > Storage & databases > D1 > fedregintel-subscribers > Studio lets the owner inspect or remove records.
Keep exports outside the repository and outside the public website.

The Worker accepts POST /signup, checks the website origin, validates email and consent,
verifies a hostname/action-bound Turnstile token, and stores a deduplicated signup.
There is no list-reading API, email sender, scheduled campaign, or email-provider connection.
TURNSTILE_SECRET is a Cloudflare secret; never put it in wrangler.jsonc or git.
Records are marked pending-launch-unverified because no confirmation email is sent.

Before launching email: select a provider, establish a valid postal address and unsubscribe handling,
review stored consent, verify addresses as appropriate, and explicitly authorize sending.
The existing newsletter drafts do not send mail and must not be scheduled while email is on hold.

Test: node --test tests/signup.test.mjs
Deploy collector: wrangler deploy (from newsletter/collector; authenticated Cloudflare account required).
Create schema on initial setup only: wrangler d1 execute fedregintel-subscribers --remote --file schema.sql
The public site still deploys through GitHub Pages. No Cloudflare hosting/DNS change is required.
