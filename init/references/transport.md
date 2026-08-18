# Getting a project in and out

Two ways in, one way out. Read this when a project arrives by an unfamiliar route, when a
fetch misbehaves, or when deciding which route to suggest.

## In — 1. The user uploads the zip

The simple path, and the one to assume by default. The user drags the file into the
conversation; it lands under `/mnt/user-data/uploads/`. Point `open.py` at it:

```bash
python3 scripts/open.py /mnt/user-data/uploads/2026-08-18-1417_emr-ai-course.zip
```

**This needs no connector at all.** It works where none is configured, where one exists
but is read-only, and where policy forbids connecting cloud storage to an assistant
entirely. Nothing about the design depends on a connector — that is worth remembering
before proposing anything more elaborate.

The one failure worth naming: the archive must arrive **as a file**, not as pasted text.
Pasted into a message, the binary is gone — deflate streams and git objects do not survive
a text round trip, even though the `PK` header at the start still looks like a zip.
`open.py` refuses it rather than half-reading it. If that happens, ask for the file itself
rather than trying to reconstruct anything.

## In — 2. Fetched from cloud storage

Saves the user a download when a readable connector is available. It is a convenience, not
a requirement.

**Find the current release.** List the project folder and take the **newest filename**.
Releases are named `YYYY-MM-DD-HHMM_slug.zip`, so a plain string sort puts the current one
last.

Never sort by modified time. A three-week-old zip copied in from elsewhere carries today's
timestamp — the filename is what someone meant, the modified time is a side effect of the
filesystem.

**Two releases with close stamps that look forked?** Do not take the newest. Fetch both and
follow `references/merging.md`; taking the newest there discards real work.

**Download it.** Ask the connector for a temporary download URL and hand it to `open.py`
with whatever checksum the platform reported beside it:

```bash
python3 scripts/open.py "https://…" --sha256 e6d429d1…
```

These URLs are typically **single-use, consumed by the first request of any method** — no
HEAD, no preflight, no retry. If one is spent, request a fresh one instead of reusing it.

Without a checksum `open.py` says the bytes are unverified rather than implying otherwise.
Silent truncation looks exactly like a normal download until git refuses to open the
repository.

## Out — always by hand

There is no second path here. The connector cannot write the zip back.

This is not one platform's gap. Checking the tool surfaces directly: Dropbox's file
creation refuses an occupied path outright and accepts text content only; Google Drive's
update operation carries a title and a parent folder but **no content field**. Different
vendors, same shape — file APIs exposed to assistants are read-and-create, not
read-and-write, and enterprise policy usually narrows that further to read-only.

So releasing means handing the file back with `present_files` and letting the user put it
in the folder. Say it in one line: **don't replace anything, just add it.**

Because that step can be skipped, check for it on the next open: if the newest file in the
folder predates the last release handed over, say so plainly. A release that never made it
back is invisible otherwise, and the next session would silently build on stale work.

## If writing back becomes possible

Everything above describes the tool surfaces as they are, not a law. If a connector does
expose a binary upload — check, do not assume — then use it. Closing the loop removes the
one step that gets skipped, and the check for "a release that never made it back" stops
being needed.

Two things do **not** change:

**Still create, never overwrite.** Upload as a new dated filename exactly as before. An
overwrite is silent about whatever was there — you cannot know the folder was untouched
since the fetch. Creating means a collision shows up as two archives side by side, visible
and recoverable. Automation removes the user's button press; it does not remove the
discipline that makes the button press safe.

**Still confirm before writing.** Putting a file into someone's cloud storage is visible to
them and to anyone sharing the folder. Say what will be created and where, then do it.

Before relying on any of this, verify the connector actually offers it: a tool that takes
text content only will accept a base64 blob or a mangled string and produce a file that is
not a valid archive, which is worse than refusing.

## Which to suggest

Default to whatever the user is already doing. If they name a cloud path, fetch it. If they
drag a file in, use it. Do not talk someone through connecting cloud storage in order to
save them one download — the upload half stays manual either way, so the connector removes
half a step, not a step.
