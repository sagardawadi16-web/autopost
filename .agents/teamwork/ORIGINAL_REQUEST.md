# Original User Request

## 2026-09-30T17:51:48Z

Build an end-to-end automated pipeline producing viral @AuralyEditsYT style comparison Shorts ("Normal Save VS Genuine Love" emotional heroism theme), offloading raw footage and production archives to sagardawadi10@gmail.com Google Drive to preserve local disk space, and scheduling releases on YouTube.

Working directory: c:/Users/LENOVO/Downloads/autopost
Integrity mode: development

## Requirements

### R1. Scenario & Story Auto-Creation
- Automatically formulate contrasting emotional heroism story concepts (e.g., standard everyday rescue vs extraordinary animal/human loyalty & devotion).
- Structure each story into a clear two-part arc: Part 1 ("Normal Save 🥶") establishing baseline tension, transitioning into Part 2 ("Genuine Love ❤️") delivering high-impact emotional resolution.

### R2. Media Sourcing & Dynamic Audio Assembly
- Source and curate real dynamic video clips online (royalty-free/public domain/creative commons footage), enhanced with lightweight zero-cost AI assistance where appropriate.
- Build a nonspoken soundscape driven by dramatic music switches (low-key suspenseful build transitioning sharply into an emotional orchestral/piano drop) accompanied by sound effects (heartbeats, whooshes, impacts).

### R3. High-Retention 9:16 Short Video Rendering
- Render vertical 1080x1920 video with high-visibility top comparison headers and animated on-screen captions synced to key visual moments.
- Ensure smooth visual transitions and color grading between the two contrasting segments.

### R4. Google Drive Cloud Storage Integration
- Establish Google OAuth2 authentication for sagardawadi10@gmail.com with Google Drive API permissions.
- Automatically upload and archive the full production package (raw source footage, audio stems, project metadata, and final rendered MP4) into an organized Drive folder hierarchy.

### R5. YouTube Scheduled Release
- Integrate with YouTube Data API to stage and schedule the rendered Short for automated publishing with optimized metadata (title, description, tags, and hashtags).

## Acceptance Criteria

### Video Quality & Structure
- [ ] Rendered video is 1080x1920 (9:16 aspect ratio), between 20 and 50 seconds in length, with valid video and audio streams verified by FFprobe.
- [ ] Video exhibits distinct two-segment structure with top comparison banner text ("Normal Save" vs "Genuine Love") and nonspoken music/SFX track.

### Google Drive Offload
- [ ] OAuth authentication completes and authenticates with sagardawadi10@gmail.com.
- [ ] Google Drive API returns status 200 verifying files exist in the designated cloud folder.

### Scheduled Publishing
- [ ] YouTube API returns a valid video ID and confirmation of scheduled publishing status.
