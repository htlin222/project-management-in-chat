#!/usr/bin/env python3
"""Pack a project for release.

Commits anything outstanding, tags the released commit, archives the directory
INCLUDING .git, then reopens the archive and verifies it before handing it over.

Why Python rather than the `zip` command: Info-ZIP writes non-ASCII filenames as UTF-8
bytes but does NOT set the ZIP general-purpose bit 11 that declares them as UTF-8 — and
`-UN=UTF8` does not fix it. Per the spec a reader must then decode them as CP437, so a
strict reader sees mojibake, and a reader that sanitises mojibake drops the characters
entirely: 專案 vanishes and `demo-專案/筆記.md` arrives as `demo-/.md`. Linux `unzip`
guesses well enough to hide this, which is exactly what makes it dangerous. Python's
zipfile sets the flag correctly, and verify_flags() below refuses to hand over an archive
where it is missing.

Usage:
    release.py <project-dir> [output-dir]
    RELEASE_MESSAGE="確認長庚時間" release.py <project-dir>

Exit codes: 0 ok, 1 failed.
"""

import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path


def git(repo, *args, check=True):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if check and r.returncode != 0:
        fail(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def fail(msg):
    print(f"FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def pack(src: Path, zip_path: Path):
    """Archive src and everything under it, preserving modes and UTF-8 names."""
    root = src.parent
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames.sort()
            here = Path(dirpath)
            # Directory entries keep empty folders (資料/ with only a .keep still needs
            # its parent) and make the archive readable when listed.
            z.write(here, here.relative_to(root).as_posix() + "/")
            for name in sorted(filenames):
                p = here / name
                if p.is_symlink():
                    fail(f"symlink in project: {p} — resolve it before releasing")
                info = zipfile.ZipInfo(
                    p.relative_to(root).as_posix(),
                    date_time=time.localtime(p.stat().st_mtime)[:6],
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (p.stat().st_mode & 0xFFFF) << 16
                z.writestr(info, p.read_bytes())


def verify_flags(zip_path: Path):
    """Every non-ASCII name must declare itself UTF-8, or readers will mangle it."""
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if not info.filename.isascii() and not (info.flag_bits & 0x800):
                fail(f"UTF-8 flag missing on {info.filename!r} — names would be mangled")


def check_ascii(src: Path):
    """Structure must be ASCII; report anything else.

    Correct UTF-8 flags make the archive valid, but the zip still crosses browser
    downloads, cloud storage, and whatever upload path comes next, any of which can
    mangle non-ASCII on its own. An all-ASCII structure makes that class of failure
    absent rather than merely handled.

    Root and structural files are hard failures because a mangled directory name breaks
    every path beneath it. A mangled document name costs one file, so those are reported
    and allowed through — blocking 講義草稿.docx would be worse than the risk.
    """
    if not src.name.isascii():
        fail(f"project directory '{src.name}' is not ASCII. A mangled root name breaks "
             f"every path under it. Rename it to an ASCII slug (contents stay in any "
             f"language) and release again.")

    offenders = []
    for dirpath, dirnames, filenames in os.walk(src):
        if ".git" in dirnames:
            dirnames.remove(".git")
        here = Path(dirpath)
        for d in dirnames:
            if not d.isascii():
                fail(f"directory '{(here / d).relative_to(src)}' is not ASCII — a "
                     f"mangled directory name breaks every path beneath it")
        for f in filenames:
            if not f.isascii():
                offenders.append(str((here / f).relative_to(src)))
    return offenders


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 1

    src = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "/mnt/user-data/outputs")
    if not src.is_dir():
        fail(f"not a directory: {src}")
    if not (src / ".git").is_dir():
        fail(f"no .git in {src.name} — git init and make a first commit before releasing")

    name = src.name
    non_ascii = check_ascii(src)

    # Uncommitted work must land in history, or it is invisible to any later comparison.
    if git(src, "status", "--porcelain"):
        print("committing outstanding changes...")
        git(src, "add", "-A")
        git(src, "commit", "-qm", os.environ.get("RELEASE_MESSAGE", "封存前自動提交"))

    # Stamp first, name second. In a folder holding one project's releases the name is a
    # constant and carries no ordering; the stamp leading makes it the sort key outright
    # and survives a rename. Hyphens inside, one underscore as delimiter, so the tag name
    # is literally the filename prefix and a project name containing _ or - stays
    # unambiguous.
    stamp = time.strftime("%Y-%m-%d-%H%M")
    out.mkdir(parents=True, exist_ok=True)
    existing_tags = git(src, "tag").splitlines()
    if stamp in existing_tags or (out / f"{stamp}_{name}.zip").exists():
        stamp += time.strftime("%S")

    zip_path = out / f"{stamp}_{name}.zip"
    git(src, "tag", "-a", stamp, "-m", os.environ.get("RELEASE_MESSAGE", f"封存 {stamp}"))

    head = git(src, "rev-parse", "HEAD")
    commits = git(src, "rev-list", "--count", "HEAD")

    pack(src, zip_path)
    verify_flags(zip_path)

    # Verify by actually reopening it. Losing .git is silent at pack time and only shows
    # up much later, when two versions turn up with no shared history to compare.
    import shutil
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp)
        back = tmp / name
        if not (back / ".git").is_dir():
            fail(".git missing from archive")
        if subprocess.run(["git", "fsck", "--no-progress"], cwd=back,
                          capture_output=True).returncode != 0:
            fail("repository corrupt in archive")
        if git(back, "rev-parse", "HEAD") != head:
            fail("HEAD mismatch in archive")
        if git(back, "rev-list", "--count", "HEAD") != commits:
            fail("commit count mismatch in archive")
        if stamp not in git(back, "tag").splitlines():
            fail(f"tag {stamp} missing from archive")
        names = zipfile.ZipFile(zip_path).namelist()
        if not any(n.startswith(f"{name}/") for n in names):
            fail("archive root does not match project name")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    size = zip_path.stat().st_size
    print(zip_path)
    print(f"  tag: {stamp}   commits: {commits}   head: {head[:7]}   "
          f"size: {size // 1024}K   verified")

    if non_ascii:
        print(f"  note: {len(non_ascii)} file name(s) contain non-ASCII characters. They "
              f"are flagged correctly and open in any conforming reader, but an upload "
              f"path could still mangle them:")
        for n in non_ascii[:5]:
            print(f"    {n}")
        if len(non_ascii) > 5:
            print(f"    ... and {len(non_ascii) - 5} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
