# FedReg Intel

Website for [FedReg Intel](https://www.youtube.com/@FedRegIntel), served at
[fedregintel.com](https://fedregintel.com).

- `public/index.html`: home page
- `public/privacy.html`: privacy policy for the FedReg Intel publishing app

The site is plain static HTML. Cloudflare Workers deploys the `public/` folder
(see `wrangler.jsonc`) whenever `main` changes.
