# WhatiflyHQ daily video pipeline

This public repository runs a free daily What If rendering and publishing pipeline. GitHub Actions renders each episode on a hosted runner with Pillow, espeak-ng, and FFmpeg. The Make scenario downloads the temporary MP4 and schedules the YouTube upload for 6:00 PM Asia/Kolkata; after Make confirms success, GitHub Actions removes the MP4 from `main` and verifies it is absent.

The daily workflow starts at 9:00 AM Asia/Kolkata. The `MAKE_WEBHOOK_URL` is stored as a repository Actions secret and must never be committed.

The requested 19:6 output is widescreen, so YouTube classifies it as a regular video rather than a Short. Episode metadata still carries `#shorts` as requested.
