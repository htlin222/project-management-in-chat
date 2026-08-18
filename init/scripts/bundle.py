#!/usr/bin/env python3
"""Put the manual inside the project, so it travels in the zip.

A release is opened wherever the user happens to be — another Claude surface, another
vendor's agent, a laptop with nothing installed. The skill that knows how this project
works may not be there. So a copy of it rides along inside the archive, at the two paths
agents actually look in:

    <project>/.claude/skills/init/     Claude Code and Claude apps
    <project>/.agent/skills/init/      the vendor-neutral location
    <project>/HOUSEKEEPING.md          the front door, for whoever unpacks it

All of them are real files, not symlinks. In the source repository those same paths ARE
symlinks to the single copy under `init/`, which is right for git and wrong for a zip:
Python's `extractall` does not restore a symlink, it writes a regular file containing the
target path, so the manual would arrive as a one-line text file pointing nowhere.
Duplicating six small files is cheap; a manual that unpacks broken is not.

Nothing here overwrites. A file that is missing gets installed; a file that differs is
reported and left alone, because the point of shipping the manual is that it can be
maintained on the other side, and silently replacing the user's edits with whatever
version happens to be installed here would defeat that. `force=True` (open.py
--refresh-skill) is the deliberate way to take this copy instead.
"""

import shutil
from pathlib import Path

# Where agents look for skills. Both are populated; neither is authoritative over
# the other.
SKILL_DIRS = (".claude/skills", ".agent/skills")

# Belongs at the project root, not buried two directories down inside a skill folder —
# it is the file a person sees first when they unpack the zip, and it exists to tell
# them how to call the skill. Installed once, at the top.
ROOT_FILES = ("HOUSEKEEPING.md",)

SKIP_DIRS = {"__pycache__", ".git", ".claude", ".agent"}

# Bundled copies are never executable, even though the originals are. `extractall` does
# not restore permission bits, so an executable file comes back without them and git
# reports a mode change on every single open — which would commit as 手動編輯 and make
# that signal, the one that says the user edited something outside a session, worthless.
# Nothing is lost: the scripts are invoked as `python3 <path>`.
BUNDLED_MODE = 0o644


def skill_root() -> Path:
    """The skill directory this script belongs to — scripts/ is one level down."""
    return Path(__file__).resolve().parent.parent


def skill_files(root: Path):
    """Relative paths of everything that makes up the manual."""
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.as_posix() in ROOT_FILES:
            continue  # installed at the project root instead
        if p.is_file() and p.suffix != ".pyc":
            yield rel


def install(project: Path, force: bool = False):
    """Copy the manual into the project. Returns (added, replaced, differing)."""
    src = skill_root()
    added, replaced, differing = [], [], []

    def place(s: Path, d: Path):
        here = str(d.relative_to(project))
        if not d.exists():
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(s, d)
            d.chmod(BUNDLED_MODE)
            added.append(here)
        elif d.read_bytes() != s.read_bytes():
            if force:
                shutil.copyfile(s, d)
                d.chmod(BUNDLED_MODE)
                replaced.append(here)
            else:
                differing.append(here)

    for base in SKILL_DIRS:
        dst = project / base / src.name
        try:
            if dst.exists() and dst.resolve() == src:
                continue  # running the copy that is already in place
        except OSError:
            pass
        for rel in skill_files(src):
            place(src / rel, dst / rel)

    for name in ROOT_FILES:
        if (src / name).is_file():
            place(src / name, project / name)

    return added, replaced, differing


def report(added, replaced, differing):
    """Print what install() did, in the one shape both scripts use."""
    if added:
        print(f"  manual bundled: {len(added)} file(s) into "
              f"{' and '.join(SKILL_DIRS)}")
    if replaced:
        print(f"  manual refreshed: {len(replaced)} file(s) overwritten")
    if differing:
        print(f"  note: {len(differing)} bundled manual file(s) differ from the "
              f"installed skill and were left as they are:")
        for n in differing[:5]:
            print(f"    {n}")
        if len(differing) > 5:
            print(f"    ... and {len(differing) - 5} more")
        print("    Run open.py --refresh-skill to take the installed version instead.")
