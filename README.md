# WhatiflyHQ temporary video host

This public repository contains the source for a free, manual-only daily What If rendering and publishing pipeline. GitHub Actions renders an episode locally on its hosted runner using Pillow, espeak-ng, and FFmpeg. The Make scenario then downloads a temporary MP4, schedules the upload to YouTube at 6:00 PM Asia/Kolkata, removes the MP4 from `main`, and checks that the file is absent.

## One-time setup
1. In GitHub Actions repository secrets, add `MAKE_WEBHOOK_URL` with the webhook URL from the Make scenario.
2. After the renderer is verified, enable its 9:00 AM Asia/Kolkata schedule.

The workflow is manual-only until the secret and final checks are completed. Never commit the webhook URL or credentials.

The requested 19:6 output is widescreen, so YouTube classifies it as a regular video rather than a Short. The episode metadata still carries `#shorts` as requested.
