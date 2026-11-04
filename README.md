# WhatiflyHQ cloud Shorts pipeline

This branch adds a cloud-first, free-to-run vertical Shorts workflow while preserving the original renderer and publishing handoff.

## New cloud workflow

- Workflow: `.github/workflows/cloud-daily-shorts.yml`
- Renderer: `automation/cloud_render.py`
- Output: **720 × 1280 (9:16)**, about 20 seconds, MP4 with narration.
- Rendering: GitHub-hosted Ubuntu runner + Pillow + espeak-ng + FFmpeg. No local PC or GPU required.
- Publishing: Make webhook continues to handle the YouTube upload and scheduled publish.
- Schedule: daily at **9:00 AM Asia/Kolkata**, with requested publishing time **6:00 PM Asia/Kolkata**.
- Temporary MP4: uploaded to the repository branch only long enough for Make to fetch it, then deleted after Make confirms scheduling. Git history can retain old blobs, so do not treat this as a private file-hosting method.

## AI with fallback

The renderer uses the curated, fact-sourced episode bank in `automation/render.py` as a safe baseline. If you configure an OpenAI-compatible chat-completions API endpoint, it may rewrite the narration and seven caption beats. The model is instructed to preserve the existing facts and sources.

If the AI key/model/endpoint is absent, the provider rate-limits, the network fails, or its output fails script checks, the renderer automatically uses the curated narration. AI is optional and **not required for the daily job to complete**.

Optional repository Actions secrets:
- `AI_API_URL`: full OpenAI-compatible chat completions endpoint, such as your provider's `/v1/chat/completions` URL.
- `AI_API_KEY`: provider key. Never commit it.
- `AI_MODEL`: provider model name.

These secrets are optional. Use only a provider whose free usage terms you understand; free quotas are not guaranteed unlimited.

## Required setup

In **Settings → Secrets and variables → Actions**, add:

- `MAKE_WEBHOOK_URL`: your existing Make webhook that accepts the handoff payload and returns JSON with `status: "scheduled"` and a `video_id`.

Optional: set `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL` for free-tier AI. If omitted, deterministic fallback is used.

The Make scenario must fetch `video_url`, upload to the connected YouTube account, and schedule using `publish_at`. Verify that scenario is configured before enabling the daily schedule. GitHub Actions cannot create or authorize the YouTube/Make connection on your behalf.

## First run / rollout

1. Review this branch and merge it into `main` when ready.
2. Confirm the Make webhook is active and returns `status: scheduled` plus `video_id`.
3. Add the required `MAKE_WEBHOOK_URL` secret.
4. Optionally add the AI secrets.
5. Run **Cloud WhatiflyHQ Shorts → Run workflow** manually.
6. Check the output MP4 and storyboard/report before relying on daily automation.

## Important limitations

- This is a **free-tier design, not a promise of unlimited cloud compute**. GitHub Actions usage and any hosted AI provider have quotas/terms.
- Current visual output is a lightweight illustrated scene renderer, not the high-end Three.js cinematic style in the Faceless Shorts ZIP. This keeps cloud CPU/render time manageable.
- The fallback uses a finite set of researched source scripts, rotates the bank when exhausted, and changes the setting. It does not invent unlimited new scientific premises.
- The workflow automatically schedules publication through your Make scenario. Test with a private/unlisted upload or disable the schedule until you have verified the scenario and channel settings.
- A vertical video under 3 minutes is eligible to be classified as a YouTube Short under current YouTube rules; verify current platform requirements before publishing.

## Original workflow

The original `.github/workflows/daily-what-if.yml` and `automation/render.py` remain unchanged. That renderer still produces 19:6 widescreen videos and uses the earlier three-premise rotation.
