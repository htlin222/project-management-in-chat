#!/usr/bin/env python3
"""Fetch and open a project release.

The mirror of release.py. Opening has four checks that are easy to skip and whose
failure is silent — a truncated download, names that lost their non-ASCII characters
upstream, a missing .git, and the user's own uncommitted edits. Each one only surfaces
much later, as a corrupt repo or a reconciliation with nothing to reconcile against.
Bundling them here means they cannot be forgotten.

Opening also makes sure the project carries its own manual — see bundle.py. A release
that lands on a platform where this skill is not installed is still workable, because the
rules travel inside the zip.

Usage:
    open.py <url-or-path> [--sha256 HASH] [--dest DIR] [--name EXPECTED_ROOT]
            [--refresh-skill]

    open.py https://…/file --sha256 e6d4…      fetch, verify, unpack
    open.py ./2026-08-18-1417_emr-ai-course.zip   local file, same checks

Download URLs from cloud connectors are usually single-use and consumed by the first
request of any method — no HEAD, no preflight, no retry. If one is spent, get a new one.

Exit codes: 0 ok, 1 failed.
"""

import sys

# Set before importing the sibling module: writing bytecode would leave a __pycache__
# directory inside the project, which then rides into git and into the next release as
# noise. Nothing here is hot enough to need it.
sys.dont_write_bytecode = True

import argparse
import hashlib
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import bundle


def fail(msg):
    print(f"FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and r.returncode != 0:
        fail(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def dropbox_content_hash(path: Path) -> str:
    """Dropbox's block hash: sha256 of the concatenated sha256 of each 4MB block."""
    outer = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            outer.update(hashlib.sha256(chunk).digest())
    return outer.hexdigest()


def fetch(url: str, dest: Path):
    """One request, no retry — these URLs are typically single-use."""
    r = subprocess.run(
        ["curl", "-sS", "--fail", "-o", str(dest), url], capture_output=True, text=True
    )
    if r.returncode != 0:
        fail(f"download failed: {r.stderr.strip()}\n"
             f"       If the link was already used or has expired, request a fresh one.")
    if not dest.exists() or dest.stat().st_size == 0:
        fail("downloaded file is empty")


def check_names(zip_path: Path) -> str:
    """Return the archive root, refusing anything that looks encoding-damaged.

    Names that lost characters upstream produce a working archive with wrong paths —
    'demo-' where 'demo-專案' belongs, or a bare '.md'. Building history on top of that
    is worse than stopping.
    """
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        if not names:
            fail("archive is empty")
        for info in z.infolist():
            base = Path(info.filename.rstrip("/")).name
            if base.startswith(".") and base.count(".") == 1 and len(base) <= 4 \
                    and base not in {".git", ".keep", ".gitignore"}:
                fail(f"entry {info.filename!r} looks like it lost characters from its "
                     f"name in transit — ask for the file again rather than working "
                     f"from a damaged copy")
        roots = {n.split("/")[0] for n in names}
        if len(roots) != 1:
            fail(f"expected a single top-level directory, found {sorted(roots)}")
        root = roots.pop()
        if root.endswith("-") or root.endswith("_"):
            fail(f"archive root {root!r} ends mid-word — characters were probably "
                 f"stripped in transit; ask for the file again")
        return root


def main():
    ap = argparse.ArgumentParser(description="Fetch and open a project release.")
    ap.add_argument("source", help="download URL or local zip path")
    ap.add_argument("--sha256", help="expected content hash reported by the platform")
    ap.add_argument("--dest", default="/home/claude", help="where to unpack")
    ap.add_argument("--name", help="expected archive root, if known")
    ap.add_argument("--refresh-skill", action="store_true",
                    help="overwrite the bundled manual with the installed version "
                         "(default: add what is missing, never replace)")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp())
    try:
        if urlparse(args.source).scheme in ("http", "https"):
            zip_path = tmp / "download.zip"
            fetch(args.source, zip_path)
        else:
            zip_path = Path(args.source).resolve()
            if not zip_path.is_file():
                fail(f"no such file: {zip_path}")

        size = zip_path.stat().st_size

        if args.sha256:
            got = dropbox_content_hash(zip_path)
            plain = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            if args.sha256 not in (got, plain):
                fail(f"checksum mismatch — the download is truncated or corrupt\n"
                     f"       expected {args.sha256}\n       got      {got}")
            print(f"  checksum ok ({size // 1024}K)")
        else:
            print(f"  {size // 1024}K downloaded — no checksum given, integrity "
                  f"unverified")

        if not zipfile.is_zipfile(zip_path):
            fail("not a valid zip — if it was pasted as text rather than transferred as "
                 "a file, the binary content is gone; send the file itself")

        root = check_names(zip_path)
        if args.name and root != args.name:
            fail(f"archive root is {root!r}, expected {args.name!r}")

        dest = Path(args.dest) / root
        if dest.exists():
            fail(f"{dest} already exists — move it aside before opening another copy, "
                 f"or the two will be confused for one")

        with zipfile.ZipFile(zip_path) as z:
            z.extractall(args.dest)

        if not (dest / ".git").is_dir():
            print("  no .git — first-time conversion; initialising")
            git(dest, "init", "-q")
            git(dest, "add", "-A")
            git(dest, "commit", "-qm", "現有內容")
        else:
            if subprocess.run(["git", "fsck", "--no-progress"], cwd=dest,
                              capture_output=True).returncode != 0:
                fail("repository is corrupt — the archive did not survive transit")
            # Edits made outside a session are invisible to every later comparison and
            # would be silently discarded by a merge. Commit them before anything else.
            if git(dest, "status", "--porcelain"):
                print("  uncommitted edits found — committing as 手動編輯")
                git(dest, "add", "-A")
                git(dest, "commit", "-qm", "手動編輯")

        # The manual rides inside the project so the next platform needs nothing
        # installed. Adds what is missing; never silently replaces an edited copy.
        added, replaced, differing = bundle.install(dest, force=args.refresh_skill)
        bundle.report(added, replaced, differing)
        if added or replaced:
            git(dest, "add", "-A")
            git(dest, "commit", "-qm", "帶上說明書：.claude/skills 與 .agent/skills")

        print(dest)
        print(f"  commits: {git(dest, 'rev-list', '--count', 'HEAD')}   "
              f"head: {git(dest, 'rev-parse', 'HEAD')[:7]}")
        tags = git(dest, "tag").splitlines()
        if tags:
            print(f"  newest release tag: {sorted(tags)[-1]}")
        print(f"  last: {git(dest, 'log', '-1', '--format=%ad %s', '--date=short')}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
