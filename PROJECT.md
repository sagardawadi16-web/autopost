# Project: Viral Comparison Shorts Automation Pipeline (@AuralyEditsYT Style)

## Architecture
The comparison Shorts pipeline automates the end-to-end production of viral "Normal Save VS Genuine Love" emotional heroism comparison Shorts:
1. **Story Director** (`src/comparison/story_director.py`): Formulates contrasting two-part emotional heroism narratives using Gemini with offline template fallbacks.
2. **Media & Audio Engine** (`src/comparison/media_curator.py`, `src/comparison/soundscape_engine.py`): Sources dynamic video clips, composes nonspoken dynamic audio with dramatic build-to-drop switch, and generates/layers SFX (heartbeats, whooshes, impacts).
3. **9:16 Video Compositor** (`src/comparison/video_compositor.py`, `src/comparison/subtitle_styler.py`): Renders 1080x1920 vertical video with top comparison badges, cool-to-warm color grading, xfade transition, and animated ASS captions.
4. **Cloud Storage Offload** (`src/storage/drive_manager.py`): Authenticates `sagardawadi10@gmail.com` with Google Drive API, uploads full production archive (raw clips, stems, metadata, final MP4), verifies cloud presence (HTTP 200), and prunes local scratch files to preserve disk space.
5. **YouTube Scheduled Release** (`src/uploader/youtube_upload.py`, `src/comparison/seo.py`): Schedules private Shorts releases via YouTube Data API v3 (`publishAt`) with optimized SEO metadata.
6. **Master Pipeline & Quality Guard** (`src/comparison_pipeline.py`, `src/quality/checkpoint_guard.py`): Glues all stages with anti-drift validation.

```
[Story Director] ──> [Media Curator & Soundscape Engine]
                                │
                                ▼
                    [9:16 Video Compositor]
                                │
          ┌─────────────────────┴─────────────────────┐
          ▼                                           ▼
[Google Drive Offload]                    [YouTube Scheduled Release]
 (sagardawadi10@gmail.com)                 (publishAt, private status)
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Story Scenario Auto-Creation | Formulate contrasting emotional heroism story concepts | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Two-Part Narrative Arc | Structure into Part 1 ("Normal Save 🥶") vs Part 2 ("Genuine Love ❤️") | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Dynamic Media Sourcing | Curate dynamic video clips online (CC/royalty-free) with AI fallback | M2 | ORIGINAL_REQUEST §R2 |
| 4 | Nonspoken Dynamic Audio | Suspenseful build transitioning into emotional orchestral/piano drop | M2 | ORIGINAL_REQUEST §R2 |
| 5 | Synchronized SFX Layering | Heartbeats, whooshes, and impact drops synced to transitions | M2 | ORIGINAL_REQUEST §R2 |
| 6 | 9:16 Vertical Rendering | 1080x1920 rendering (20-50s) with adaptive blurred canvas | M3 | ORIGINAL_REQUEST §R3 |
| 7 | Top Comparison Headers | Distinct top badge overlays ("Normal Save" vs "Genuine Love") with emojis | M3 | ORIGINAL_REQUEST §R3 |
| 8 | Animated On-Screen Captions | Styled ASS subtitles synced to video moments in safe zones | M3 | ORIGINAL_REQUEST §R3 |
| 9 | Dual Color Grading & Transitions | Cool/desaturated vs warm golden glow with clean black dip transition | M3 | ORIGINAL_REQUEST §R3 |
| 10 | Google Drive OAuth2 Auth | Authenticate `sagardawadi10@gmail.com` with Drive scopes | M4 | ORIGINAL_REQUEST §R4 |
| 11 | Cloud Storage Hierarchy Offload | Upload raw footage, audio stems, metadata, and final MP4 | M4 | ORIGINAL_REQUEST §R4 |
| 12 | Local Disk Cleanup | Verify cloud archive (HTTP 200) and purge local raw clips to save disk | M4 | ORIGINAL_REQUEST §R4 |
| 13 | YouTube Scheduled Publishing | Schedule release via YouTube API (`publishAt` + `privacyStatus="private"`) | M5 | ORIGINAL_REQUEST §R5 |
| 14 | Comparison SEO Metadata | Generate titles, descriptions, tags, and hashtags for comparison theme | M5 | ORIGINAL_REQUEST §R5 |
| 15 | Pipeline CLI & Checkpoint Guard | Master pipeline execution and quality gatekeeper assertions | M6 | GEMINI.md & Invariants |
| 16 | E2E Test Suite (Tiers 1-4) | Independent opaque-box test suite verifying all acceptance criteria | M7 / E2E Track | ORIGINAL_REQUEST §Acceptance Criteria |
| 17 | Adversarial Hardening (Tier 5) | White-box edge case testing and forensic integrity verification | M7 | Dual Track Protocol |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Story Concept & Scenario Director | Two-part emotional story schema, Gemini prompt + offline templates | none | PLANNED |
| M2 | Media Sourcing & Dynamic Audio Soundscape | Video sourcing cascade + nonspoken dual-phase audio + SFX generator | M1 | PLANNED |
| M3 | 9:16 Video Compositor & Subtitles | 1080x1920 rendering, badges, color grading, ASS captions, xfade | M1, M2 | PLANNED |
| M4 | Google Drive Cloud Storage Offload | Drive OAuth2 for sagardawadi10@gmail.com, folder hierarchy, disk purge | none | PLANNED |
| M5 | YouTube Scheduled Publishing | YouTube API `publishAt`, private status enforcement, SEO metadata | none | PLANNED |
| M6 | Master Comparison Pipeline & Gates | `src/comparison_pipeline.py` CLI and `src/quality/checkpoint_guard.py` | M1, M2, M3, M4, M5 | PLANNED |
| M7 | E2E Verification & Adversarial Hardening | 100% E2E test suite pass + Tier 5 adversarial tests + Forensic audit | M6, E2E Track | PLANNED |

## Interface Contracts

### Story Director ↔ Media Curator & Soundscape Engine
- **Data Structure**: `ComparisonStory` dataclass
  - `story_id: str`
  - `title: str`
  - `theme: str`
  - `part1: StorySegment` (duration: float, header_text: str, tone: str, search_queries: List[str], caption_beats: List[CaptionBeat])
  - `pivot: PivotMoment` (timestamp: float, transition_effect: str, sfx: str)
  - `part2: StorySegment` (duration: float, header_text: str, tone: str, search_queries: List[str], caption_beats: List[CaptionBeat])
  - `total_duration: float` (20.0 to 50.0 seconds)

### Media & Audio ↔ 9:16 Video Compositor
- **Input Files**:
  - `part1_video: Path` (MP4 or video clip, min 720p)
  - `part2_video: Path` (MP4 or video clip, min 720p)
  - `master_audio: Path` (MP3/WAV containing mixed suspense build, pivot SFX, and emotional drop)
  - `captions_file: Path` (ASS subtitle file with safe area positioning)
  - `story_manifest: ComparisonStory`
- **Output**:
  - `rendered_video: Path` (1080x1920 vertical H.264 MP4, AAC audio, duration 20s–50s)

### Production Package ↔ Google Drive Offload
- **Package Directory**: `output/comparison_archive/{story_id}/`
  - `raw_footage/` (`part1_raw.mp4`, `part2_raw.mp4`)
  - `audio_stems/` (`suspense_build.mp3`, `emotional_drop.mp3`, `sfx_impact.wav`, `master_audio.mp3`)
  - `metadata/` (`story_manifest.json`, `youtube_metadata.json`, `render_specs.json`)
  - `final_render/` (`{story_id}_1080x1920.mp4`, `thumbnail.jpg`)
- **Return Signature**:
  - `GoogleDriveManager.upload_production_package(package_dir: Path, story_id: str) -> Dict[str, Any]`
  - Returns: `{"status": 200, "folder_id": str, "uploaded_files": List[Dict], "drive_url": str}`

### Master Pipeline ↔ YouTube Scheduled Uploader
- **Method Signature**:
  - `YouTubeUploader.upload_video(video_path: str, metadata: VideoMetadata, publish_at: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]`
  - Returns: `{"video_id": str, "url": str, "status": "scheduled"|"public"|"private", "scheduled_publish_time": Optional[str]}`

## Code Layout
```
c:/Users/LENOVO/Downloads/autopost/
├── src/
│   ├── comparison/
│   │   ├── __init__.py
│   │   ├── schemas.py                 # Story & segment data contracts
│   │   ├── story_director.py          # AI & template comparison story formulation
│   │   ├── media_curator.py           # Video footage curation & fallback generation
│   │   ├── soundscape_engine.py       # Nonspoken suspense-to-drop audio + procedural SFX
│   │   ├── subtitle_styler.py         # Mobile safe-zone ASS caption generation
│   │   ├── video_compositor.py        # FFmpeg 9:16 rendering, pill badges, color grading
│   │   └── seo.py                     # AuralyEdits comparison metadata generator
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── drive_auth.py              # Google Drive OAuth2 manager for sagardawadi10@gmail.com
│   │   └── drive_manager.py           # Cloud folder hierarchy offload & disk space cleanup
│   ├── uploader/
│   │   ├── youtube_upload.py          # Extended with publish_at scheduling
│   │   └── scheduler.py               # Stealth publish time calculation
│   ├── quality/
│   │   └── checkpoint_guard.py        # Quality checkpoints for comparison pipeline
│   └── comparison_pipeline.py         # Master CLI orchestrator
├── tests/
│   ├── e2e/
│   │   ├── test_runner.py             # E2E test runner
│   │   ├── test_tier1_features.py     # Tier 1: Feature coverage
│   │   ├── test_tier2_boundaries.py   # Tier 2: Boundary & corner cases
│   │   ├── test_tier3_combinations.py # Tier 3: Cross-feature combinations
│   │   └── test_tier4_scenarios.py    # Tier 4: Real-world application scenarios
```
