#!/usr/bin/env python3
"""Generate a Skill catalog from local Skills and external source metadata."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.json"
EXTERNAL = ROOT / "external-skills.json"
VALID_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def metadata(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"missing frontmatter: {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"unclosed frontmatter: {path}") from exc
    fields = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"\'')
    skill_id = fields.get("name", "")
    description = fields.get("description", "")
    if not VALID_ID.fullmatch(skill_id) or skill_id != path.parent.name or not description:
        raise ValueError(f"invalid name or description: {path}")
    return skill_id, fields.get("title") or skill_id.replace("-", " ").title(), description


def build():
    entries = {}
    for manifest in sorted(ROOT.glob("*/SKILL.md")):
        skill_id, title, description = metadata(manifest)
        files = [path for path in manifest.parent.rglob("*") if path.is_file()]
        if len(files) > 64:
            raise ValueError(f"too many files: {manifest.parent}")
        entries[skill_id] = {
            "id": skill_id,
            "name": title,
            "description": description,
            "path": manifest.parent.name,
            "fileCount": len(files),
        }
    external = json.loads(EXTERNAL.read_text(encoding="utf-8"))
    for item in external["skills"]:
        skill_id = item["id"]
        source = item["sourceURL"]
        if not VALID_ID.fullmatch(skill_id) or not source.startswith("https://"):
            raise ValueError(f"invalid external Skill: {skill_id}")
        if skill_id in entries:
            local = entries[skill_id]
            if any(local[key] != item[key] for key in ("name", "description", "fileCount")):
                raise ValueError(f"external metadata differs from local fallback: {skill_id}")
            local["sourceURL"] = source
        else:
            entries[skill_id] = item
    return json.dumps({"schemaVersion": 1, "skills": [entries[key] for key in sorted(entries)]},
                      ensure_ascii=False, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if index.json is stale")
    args = parser.parse_args()
    content = build()
    if args.check:
        if not INDEX.exists() or INDEX.read_text(encoding="utf-8") != content:
            raise SystemExit("index.json is out of date; run scripts/generate-index.py")
    else:
        INDEX.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
