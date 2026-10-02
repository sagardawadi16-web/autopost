"""YouTube Growth Skills Unified CLI & Agent Bridge.

Provides single-entry-point execution for all 11 YouTube agent skills:
- yt-script (hookscore.py)
- yt-package (title.py)
- yt-retention (retention.py)
- yt-viral (swipe.py)
- yt-edit (deadair.py)
- yt-chapters (chapters.py)
- yt-seo (metadata generator)
- yt-shorts (condenser)
- yt-audit (channel performance analysis)
- yt-plan (weekly content scheduler)
- yt-comment (voice responder)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# UTF-8 stdout configuration for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Standalone CLI path resilience
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("autopost.growth_skills")

SKILLS_DIR = _repo_root / ".agents" / "skills"


def run_hookscore(hook_text: str) -> Dict[str, Any]:
    """Score a hook on 5 core properties using yt-script hookscore."""
    from src.scriptwriter.evaluator import score_hook
    parts, verdict, weakest = score_hook(hook_text)
    return {
        "hook": hook_text,
        "verdict": verdict,
        "weakest_property": weakest,
        "properties": parts,
    }


def run_title_lint(title: str, thumb: Optional[str] = None) -> Dict[str, Any]:
    """Lint and score a title & thumbnail pairing using yt-package title linter."""
    from src.scriptwriter.seo import lint_title_pairing
    return lint_title_pairing(title, thumb)


def list_installed_skills() -> List[Dict[str, str]]:
    """List all installed YouTube agent skills in the repo."""
    skills = []
    if SKILLS_DIR.exists():
        for item in sorted(SKILLS_DIR.iterdir()):
            if item.is_dir() and item.name.startswith("yt-"):
                skill_file = item / "SKILL.md"
                desc = "Installed YouTube Agent Skill"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        lines = content.splitlines()
                        for line in lines:
                            if line.startswith("description:"):
                                desc = line.replace("description:", "").strip()
                                break
                    except Exception:
                        pass
                skills.append({"name": item.name, "description": desc, "path": str(item)})
    return skills


def main() -> None:
    """CLI dispatcher for YouTube growth skills."""
    parser = argparse.ArgumentParser(description="YouTube Growth Skills Unified CLI Bridge")
    parser.add_argument("--hookscore", type=str, help="Score a single video hook string")
    parser.add_argument("--lint-title", type=str, help="Lint a YouTube title")
    parser.add_argument("--thumb", type=str, help="Thumbnail text for title pairing linting")
    parser.add_argument("--list-skills", action="store_true", help="List all 11 installed YouTube agent skills")
    parser.add_argument("--audit", action="store_true", help="Run channel growth audit report")

    args = parser.parse_args()

    if args.list_skills or len(sys.argv) == 1:
        skills = list_installed_skills()
        print("\n=======================================================")
        print("  🎯 INSTALLED YOUTUBE AGENT SKILLS (11 Total)")
        print("=======================================================")
        for s in skills:
            print(f"  • {s['name']:<15} {s['description']}")
        print("=======================================================\n")
        return

    if args.hookscore:
        res = run_hookscore(args.hookscore)
        print(json.dumps(res, indent=2))
        return

    if args.lint_title:
        res = run_title_lint(args.lint_title, args.thumb)
        print(json.dumps(res, indent=2))
        return

    if args.audit:
        from src.evolution.learning_memory import StrategicLearningMemory
        memory = StrategicLearningMemory()
        report = memory.get_growth_report()
        print(json.dumps(report, indent=2))
        return


if __name__ == "__main__":
    main()
