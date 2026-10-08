# FedReg Intel

## Dashboard (September 2026)

The public website combines a Federal Register dashboard, the author's published Kindle book,
and the @FedRegIntel public video archive. Plain HTML/CSS/JavaScript; no paid dependencies.

- Rule results come directly from FederalRegister.gov's public API on page load, search, filter,
  pagination, and every five minutes while visible. Eastern calendar dates are used for deadlines.
- Search includes document type, agency, comment window, official PDFs and comment links.
- Watchlists use browser localStorage. Saved details may be stale; always check the linked source.
- `data/rules.json` is an explicitly labeled fallback snapshot of the latest 100 rules/proposals
  plus deadlines in the next seven days. It is not a complete Federal Register copy.
- `data/videos.json` was seeded with all 13 public uploads using the owner's existing local
  YouTube authorization. No credentials are present in this repo or in the site.
- `scripts/refresh_data.py` polls the public YouTube RSS feed and merges entries by video ID.
  Previously indexed entries remain. YouTube's feed is limited to recent uploads, so a prolonged
  updater outage or a burst exceeding the feed window requires a complete API backfill.
  Removed/private videos may remain in the historical index, with playback controlled by YouTube.
- GitHub Actions runs at minutes 7, 22, 37 and 52 each hour, on manual dispatch, and on
  `repository_dispatch` type `youtube-published`. Schedules can be delayed by GitHub. A stale
  archive warning appears after one hour. Source failures retain previous snapshots and fail the run.
- The workflow publishes Pages explicitly, because commits made with GITHUB_TOKEN do not trigger
  a legacy Pages build. Pages must use the **GitHub Actions** source.
- Book link: https://www.amazon.com/dp/B0HL97PYTB. Cover supplied from the author's book project.

### Local development

Python 3.12+: `python -m pip install tzdata` (needed on Windows), then
`python scripts/refresh_data.py` and `python -m http.server 8766`.
Open http://localhost:8766. JavaScript syntax: `node --check assets/app.js`.
Regression checks: `python -m unittest discover -s tests`.

### Publishing

Push to `main` to run the refresh/deploy workflow. The deploy artifact includes `index.html`, `privacy.html`, `CNAME`, `.nojekyll`, `assets/`, `data/`, and `course/`. Scripts and repository files stay out of the
Pages artifact. Never add OAuth token files, client secrets or local publishing credentials.

---

Website for [FedReg Intel](https://www.youtube.com/@FedRegIntel), served at
[fedregintel.com](https://fedregintel.com).

- `index.html`: home page
- `privacy.html`: privacy policy for the FedReg Intel publishing app

The site is static HTML hosted on GitHub Pages, deployed by GitHub Actions from `main`.
`CNAME` sets the custom domain.
