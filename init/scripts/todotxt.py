#!/usr/bin/env python3
"""Generate a todo.txt-spec-compliant *view* of a project, without touching the source.

The human-facing files carry no syntax on purpose — a person reads them and no program
does (see SKILL.md, "A line has no syntax at all"). 等 and 不確定 are words, not symbols.
That stance is not up for negotiation here: `todo.txt` and `done.txt` stay exactly as the
user wrote them.

But the same content can *also* be offered to the todo.txt ecosystem (todo.txt apps,
tod.sh, mobile clients) for free — as a **generated, derived** copy the user never edits
and never has to learn. This script writes that copy into `export/`:

    todo.txt   (root, natural language)  ──derive──▶  export/todo.txt   (spec-compliant)
    done.txt   (root, natural language)  ──derive──▶  export/done.txt   (spec-compliant)

Nothing on the human surface changes. `export/` is a projection, regenerated on every
release; deleting it loses nothing.

The mapping, kept intentionally small (the rest of the spec — (A) priority, +project —
is deferred; one project needs no +project tag, and priority lives in notes.md):

  done.txt line              →  `x <completion-date> [<creation-date>] <text>`
  todo line beginning 等       →  append ` @waiting`   (blocked on someone else)
  todo line beginning 不確定    →  append ` @uncertain` (may already be done, no record)
  leading YYYY-MM-DD          →  kept as the spec creation date (already compatible)

Every transform is idempotent: a line already in spec form is returned unchanged, so
re-exporting on each release never churns.

Usage:
    todotxt.py export <project-dir> [--today YYYY-MM-DD]   write export/{todo,done}.txt
    todotxt.py show   <project-dir> [--today YYYY-MM-DD]   print the spec view, write nothing
    todotxt.py check  <project-dir>                        report; exit 0 always (advisory)

Exit codes: 0 ok, 1 usage/IO error.
"""

import argparse
import re
import sys
import time
from pathlib import Path

DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})\b")
WAITING = "@waiting"
UNCERTAIN = "@uncertain"


def _split_leading_date(text: str):
    """Return (creation_date_or_None, remainder). A leading YYYY-MM-DD is the spec
    creation date already, so it is preserved rather than re-stamped."""
    m = DATE.match(text)
    if m:
        return m.group(1), text[m.end():].lstrip()
    return None, text


def to_spec_todo(line: str) -> str:
    """One natural-language todo line → one todo.txt-spec line. Idempotent.

    The description is kept verbatim (lossless, still human-readable); only a trailing
    machine context is added so a todo.txt reader can filter on it.
    """
    text = line.rstrip("\n")
    if not text.strip():
        return text
    date, rest = _split_leading_date(text.strip())

    tag = None
    if rest.startswith("等"):
        tag = WAITING
    elif rest.startswith("不確定"):
        tag = UNCERTAIN

    out = f"{date} {rest}" if date else rest
    if tag and tag not in out.split():
        out = f"{out} {tag}"
    return out


def to_spec_done(line: str, today: str) -> str:
    """One done/abandoned line → one todo.txt-spec completed line. Idempotent.

    Spec form: `x <completion-date> [<creation-date> ]<text>`. An already-completed line
    (starts with `x `) is returned unchanged so re-export is stable.
    """
    text = line.rstrip("\n")
    if not text.strip():
        return text
    if text.lstrip().startswith("x "):
        return text  # already spec-completed — leave it
    date, rest = _split_leading_date(text.strip())
    if date:
        return f"x {today} {date} {rest}"
    return f"x {today} {text.strip()}"


def _read_lines(path: Path):
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").splitlines()


def render(project: Path, today: str):
    """Return {name: spec_text} for whichever of todo.txt / done.txt exist."""
    out = {}
    todo = _read_lines(project / "todo.txt")
    if todo is not None:
        out["todo.txt"] = "\n".join(to_spec_todo(l) for l in todo)
    done = _read_lines(project / "done.txt")
    if done is not None:
        out["done.txt"] = "\n".join(to_spec_done(l, today) for l in done)
    return out


def export(project: Path, today: str) -> list:
    """Write the spec view into project/export/. Returns the filenames written."""
    views = render(project, today)
    if not views:
        return []
    dest = project / "export"
    dest.mkdir(exist_ok=True)
    written = []
    for name, text in views.items():
        body = text + "\n" if text and not text.endswith("\n") else text
        (dest / name).write_text(body, encoding="utf-8")
        written.append(f"export/{name}")
    return written


def main():
    ap = argparse.ArgumentParser(description="Generate a todo.txt-spec view of a project.")
    ap.add_argument("command", choices=["export", "show", "check"])
    ap.add_argument("project", help="project directory (holding todo.txt / done.txt)")
    ap.add_argument("--today", help="completion date to stamp (default: today)")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"FAILED: not a directory: {project}", file=sys.stderr)
        return 1
    today = args.today or time.strftime("%Y-%m-%d")

    if args.command == "export":
        written = export(project, today)
        if not written:
            print("  no todo.txt / done.txt at project root — nothing to export")
        else:
            print(f"  wrote {', '.join(written)} (spec-compliant, derived — never hand-edit)")
        return 0

    if args.command == "show":
        views = render(project, today)
        for name, text in views.items():
            print(f"# ---- export/{name} ----")
            print(text)
        return 0

    # check: advisory report only
    views = render(project, today)
    if not views:
        print("  no todo.txt / done.txt found")
    for name, text in views.items():
        n = len([l for l in text.splitlines() if l.strip()])
        print(f"  export/{name}: {n} spec line(s) ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
