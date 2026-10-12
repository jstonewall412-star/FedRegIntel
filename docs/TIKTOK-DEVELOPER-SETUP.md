# FedReg Intel TikTok developer setup

Prepared October 12, 2026. This guide concerns **FedReg Intel**, not Ministry of Petty.

## Verified account and application

- Developer organization: **FedReg Intel**, ID `7695545204169835521`.
- App: **FedReg Intel Uploads**, ID `7695696910073595956`.
- Sandbox: **FedReg Draft Upload Test**, ID `7695696910073628724`.
- App page: https://developers.tiktok.com/app/7695696910073595956/pending
- Sandbox page: https://developers.tiktok.com/app/7695696910073595956/sandbox/7695696910073628724
- The signed-in posting account is **@jstonewall412**. Its profile contains both FedReg Intel and Ministry of Petty posts. Two developer organizations do not create two TikTok posting accounts.

The app and sandbox exist. **No application was submitted for TikTok review. No live API upload or account authorization has been completed with this starter.** Do not treat created credentials, passing local tests, an upload response, or a prepared demo script as production approval or publication.

## Ready files and exact form answers

| Field | Value / source |
|---|---|
| App name | FedReg Intel Uploads |
| App type | Other |
| Category | News (currently selected by the owner in the portal) |
| Description (111 characters) | Review original FedReg Intel videos and send TikTok drafts for creator approval. Educational; not legal advice. |
| Platform | Desktop |
| Desktop URL | https://fedregintel.com/tiktok/ |
| Terms of Service URL | https://fedregintel.com/tiktok/terms.html |
| Privacy Policy URL | https://fedregintel.com/tiktok/privacy.html |
| App icon | `tiktok/app-icon-1024.png` (1024 × 1024 PNG, under 5 MB) |
| Login Kit Desktop redirect | `http://127.0.0.1:8769/callback/` |
| Products | Login Kit; Content Posting API with default Upload to TikTok |
| Scopes | `user.info.basic`, `video.upload` |
| Direct Post | Off; do not request `video.publish` |
| Target account | Add @jstonewall412 as a sandbox target user through TikTok's own account-consent screen |

The public URLs above are **intended deployment URLs** until the repository change is merged and the Pages deployment is verified. The existing general privacy policy is `https://fedregintel.com/privacy.html`; it mainly describes the YouTube app and email list, so it is not a substitute for the TikTok-specific policy supplied here. The deployment workflow now includes `tiktok/` in its public artifact; `tools/` and `docs/` remain outside that artifact. Keep all client secrets, access tokens, refresh tokens, OAuth codes, and source videos out of GitHub.

The icon redraws the existing FedReg Intel FR monogram at the required size, retaining its navy, white, and gold identity. Original branding reference: `social-launch/images/avatar-1000.png`. A 512px or 1000px image does not satisfy the current 1024px requirement.

## Why Desktop

The existing owner workflow is local. TikTok explicitly permits localhost Desktop callbacks and requires PKCE; the callback above is implemented in `tools/tiktok/uploader.py`, not an invented placeholder. The app uses local `FILE_UPLOAD`, so no hosted-video URL is needed. Website/terms/privacy URL ownership must still be verified in TikTok. If the application is later hosted or uses `PULL_FROM_URL`, update its architecture, privacy text, redirect configuration, and domain verification first.

## Run the real local prototype

Requires Python 3.12+; no additional Python packages.

1. Run `tools/tiktok/start.ps1`, or `python tools/tiktok/uploader.py` from the repository root.
2. Open http://127.0.0.1:8769/.
3. Enter the **sandbox** client key and client secret locally. Never paste them into chat or this guide. They stay in process memory.
4. Connect with TikTok and explicitly grant basic-profile and draft-upload access. This is a separate account-access authorization step; app creation alone does not authorize it.
5. Verify the connected display name. Preview an original MP4 (up to 64 MiB).
6. Confirm content rights, resolved fact checks, and the paired public, playable YouTube episode. Tick consent and send the draft.
7. Check the upload status; then use TikTok's inbox notification to finish caption/disclosures and the publishing decision.
8. Use Disconnect and revoke access when done. Closing the app clears local memory but does not itself revoke the TikTok grant or delete drafts.

Client credentials and tokens are not stored on disk. Duplicate/ambiguous uploads are held within the running session. After a restart, check the TikTok inbox and existing queue before retrying. No public-post endpoint or scheduler exists in this starter. The signed-in browser and sandbox target account must match the intended destination.

## Existing local materials to reuse

- `C:/Users/jarre/OneDrive/Desktop/FedReg Intel/TIKTOK-PUBLISHING.txt`: owner workflow and disclosure requirements.
- `C:/Users/jarre/OneDrive/Desktop/FedReg Intel/prepare_tiktok.py`: original vertical teaser preparation; respects unresolved fact-check holds.
- `C:/Users/jarre/OneDrive/Desktop/FedReg Intel/out/tiktok/<youtube_id>/`: MP4, caption, and publication manifest.
- `C:/Users/jarre/OneDrive/Desktop/FedReg Intel/out/tiktok/MDOurHcaBbA/video.mp4`: existing 18.312-second evergreen teaser. Its manifest records it as already published; use it only for local preview unless a deliberate sandbox duplicate is approved. Do not blindly republish it.
- Website repository: https://github.com/jstonewall412-star/FedRegIntel

YouTube remains independent of TikTok failures. Hold TikTok teasers with unresolved source facts or unconfirmed YouTube processing/playback. Finish AI-generated-content and Your brand disclosure in TikTok; the Upload API's final edit/publish flow happens there.

## Draft review explanation (paste only once the described flow is demonstrated)

FedReg Intel Uploads is an owner-operated desktop prototype for original educational videos about federal rulemaking and public comments. Login Kit requests user.info.basic to identify and display the connected account. Content Posting API requests video.upload to send a creator-selected local MP4 to TikTok as a draft after preview and explicit consent. The app checks processing status and instructs the creator to finish editing, disclosures, visibility and publishing through TikTok's inbox notification. It does not use video.publish, automate public publishing or copy arbitrary third-party content. Credentials and tokens stay in local process memory and can be revoked through Disconnect. The website provides app-specific terms and privacy details. A genuine sandbox demo must show the implemented authorization, preview, consent, transfer and inbox flow before submission.

## Required genuine demo: not recorded yet

See `docs/TIKTOK-DEMO-CHECKLIST.md`. No mock authorization or success screen should be submitted as an end-to-end API demo. The local preflight screenshot only demonstrates the implemented UI before credentials and account consent; it proves no live TikTok upload.

## Validation completed locally

- Seven uploader tests cover desktop PKCE/state, callback rejection, scope checks, no-connection/file guards, upload-host allowlist and duplicate-attempt holds.
- Thirty existing repository tests passed.
- Python compilation passed; the UI is served locally and visually inspected.
- Live credentials, account consent, upload processing, target-account ownership, and real inbox delivery remain unverified.

## Correction to the shared Ministry guide

The Ministry guide at `petty-grievances/docs/TIKTOK-DEVELOPER-SETUP.md` is a reference, not FedReg configuration. Its 512px icon and placeholder-redirect advice must not be copied here. Developer email registration is separate from the TikTok publishing account. Public Direct Post requires audit and excludes internal/private account-management utilities under TikTok's stated guidelines. Draft Upload is a different API flow and still requires approved scopes and user authorization.

## Official references (checked October 12, 2026)

- Register an app: https://developers.tiktok.com/docs/en/getting-started-create-an-app
- Desktop Login Kit / PKCE: https://developers.tiktok.com/docs/en/login-kit-desktop
- OAuth token handling: https://developers.tiktok.com/docs/en/oauth-user-access-token-management
- Upload drafts: https://developers.tiktok.com/docs/en/content-posting-api-get-started-upload-content
- Media transfer constraints: https://developers.tiktok.com/docs/en/content-posting-api-media-transfer-guide
- Basic profile fields: https://developers.tiktok.com/docs/en/tiktok-api-v2-get-user-info
- Sandbox restrictions: https://developers.tiktok.com/docs/en/add-a-sandbox
- Direct Post intended-use restrictions: https://developers.tiktok.com/docs/en/content-sharing-guidelines
