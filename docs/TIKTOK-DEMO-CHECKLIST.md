# Genuine FedReg Intel TikTok review demo

Status: **requires sandbox configuration and account consent; no end-to-end recording yet**.

TikTok asks for an MP4/MOV, at most 50 MB, showing the real integration. Record the actual desktop UI and TikTok screens after the steps below work. Do not fabricate authorizations, progress, inbox notifications, approval or posting outcomes. Keep secrets, OAuth codes, tokens and full upload URLs out of recordings.

## Before recording

- [ ] Public app overview, terms and privacy pages deployed, reachable and ownership-verified.
- [ ] 1024px app icon, News category, description and Desktop platform saved.
- [ ] Login Kit Desktop callback exactly `http://127.0.0.1:8769/callback/`.
- [ ] Content Posting API added; Direct Post remains off; scopes limited to `user.info.basic,video.upload`.
- [ ] @jstonewall412 added as a target user to **this** FedReg sandbox.
- [ ] Credentials entered privately and deliberately omitted from the recording.
- [ ] Owner authorizes the actual TikTok connection and proposed test draft.
- [ ] Test video is original, short, fact-checked and within sandbox restrictions. Do not publish a duplicate of an existing public teaser.

## Record the genuine sequence (approximately 60–120 seconds)

1. Show FedReg Intel's app overview and links to terms/privacy.
2. Open the local desktop uploader. Explain that it sends drafts; publication happens in TikTok.
3. Click Connect, show TikTok's account and requested scope consent without recording credentials, and show the real callback result.
4. Show the connected display name; confirm the intended account.
5. Select a rights-cleared original MP4 and play its preview.
6. Show the per-video consent checkbox and click Send draft only after owner approval.
7. Show the real status response; don't relabel a transfer as published.
8. Show TikTok's real inbox draft notification and editing flow. Finish disclosure/visibility choices there; publishing is not necessary unless the owner separately approves it.
9. Show Disconnect/revoke, then the app's disconnected state.

## Submission gate

Submit only when the recording corresponds to the implemented, verified flow and all required products/scopes are demonstrated. The preflight UI screenshot is useful supporting evidence but **cannot replace** this recording. TikTok approval remains a separate external decision.
