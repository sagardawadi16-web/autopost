## 📝 Summary of Changes
<!-- Provide a brief, clear summary of what this PR does and why. -->

## 🎯 Target Channels / Modules Affected
- [ ] English Pipeline (`src/pipeline.py`)
- [ ] Hindi Pipeline (`src/pipeline.py`, `src/video/hindi_visual_engine.py`)
- [ ] Studio Ghibli Engine (`src/ghibli/`, `src/ghibli_pipeline.py`)
- [ ] Comparison Shorts (`src/comparison/`)
- [ ] GitHub Actions Workflows (`.github/workflows/`)

## 🧪 Verification & Proof
<!-- Describe how you verified these changes. Paste command output or dry-run test details. -->
- [ ] Tested via CLI dry-run (`python -m src.pipeline --dry-run`)
- [ ] Tested individual stage (`python -m src.pipeline --stage <stage>`)
- [ ] Verified video resolution and audio-visual synchrony

## 📋 Checklist
- [ ] Code follows standalone CLI invariant (`sys.path.insert(0, str(_repo_root))`)
- [ ] No API keys or secrets are committed
- [ ] All new dependencies added to `requirements.txt`
