---
name: init
description: Open a single project as a zip containing a git repo, work on it in the sandbox, and release it back as a new dated zip. Use whenever the user says /init, 展開專案, 打開專案, 開一個新專案, 封存, release, uploads a project zip, or names a cloud folder to fetch one from. Also use whenever they ask 上次到哪, 這個案子怎樣了, 什麼卡住了, 下一步是什麼, 幫我記一下, or want tasks recorded or reviewed inside a project. Use it before packing or unpacking any archive containing non-ASCII filenames, because the `zip` command silently strips them and `unzip` hides the damage. Also use when two versions of a project turn up and need reconciling. Needs no cloud connector — a zip dragged into the conversation is the default route — and is built for storage that can be read but never overwritten, such as OneDrive, SharePoint, Dropbox, or Google Drive.
---

# init

One project at a time. It lives as a zip containing a git repository; it is opened into
the sandbox, worked on, and released as a **new** zip with a newer name.

The storage it comes from can be read but not overwritten. So the mapping is:

| git | here |
|---|---|
| remote | the project folder in cloud storage |
| clone / pull | download the newest zip, unpack it |
| commit | work happening in the sandbox |
| push | a new dated zip the user uploads |

There is no rejection on push. Cloud storage accepts whatever arrives — which is why
releases are **only ever added, never replace**. Uploading under a new name turns a
silent overwrite into two visible files, and two visible files can be merged.

## Filenames are where this breaks — read this before packing anything

This is not a hypothetical. It has happened, it was silent, and the obvious test missed it.

**Never pack with the `zip` command.** Info-ZIP writes non-ASCII filenames as UTF-8 bytes
but does *not* set ZIP general-purpose bit 11, the flag that declares them UTF-8. Per the
spec a reader must then decode those bytes as CP437, so it sees mojibake — and a reader
that sanitises mojibake drops the characters outright:

```
packed:    demo-專案/筆記.md
delivered: demo-/.md
```

The archive opens. Nothing errors. The names are just quietly wrong, and `.git` paths go
with them. `-UN=UTF8` does not fix it.

**Testing with `unzip` proves nothing.** Linux `unzip` guesses the encoding and displays
the names correctly regardless — which is exactly what makes it dangerous. The forgiving
tool is the one that hides this class of bug. **Verify with a strict reader**: Python's
`zipfile`, which honours the flag and shows you what a conforming reader actually sees.

`release.py` packs with Python's zipfile, which sets the flag, and refuses to hand over an
archive where any non-ASCII name lacks it. Use it. Do not hand-roll packing.

**On opening, check the names before extracting.** A root directory or filename with
characters missing — `demo-` where `demo-專案` belongs, or a bare `.md` — means the archive
lost its non-ASCII names somewhere upstream. Say so and ask for the file again rather than
working from a damaged copy and rebuilding history on top of it.

**Keep the structure ASCII, so the problem is absent rather than handled.** Correct flags
make an archive valid, but the zip still crosses browser downloads, cloud storage, and
whatever upload path comes next — any of which can mangle non-ASCII on its own, no matter
how correct the archive is. An all-ASCII structure removes the failure entirely instead of
defending against it.

`release.py` enforces this, and the asymmetry is deliberate:

- **Root and directory names — hard failure.** A mangled directory name breaks every path
  beneath it.
- **Document filenames — reported, allowed through.** A mangled filename costs one file,
  and blocking `講義草稿.docx` would be worse than the risk.

**Only names are constrained. Everything read stays in the user's language:** `notes.md`
contains 現在狀態/最可能出事/在等誰, tasks are written in Chinese, commit messages are in
Chinese. The cloud folder keeps whatever name it already has — never rename an existing
folder, which breaks paths and links people have already sent. Record it in `notes.md`
instead, and let the ASCII slug live only inside the archive.

## Opening

Trigger: `/init`, "打開病歷學會AI課", "去 Dropbox /demo 拿", or a project zip arriving.

A project arrives one of two ways:

- **The user uploads the zip** — the default, and it needs no connector at all. The file
  lands under `/mnt/user-data/uploads/`.
- **Fetched from cloud storage** — when a readable connector exists, saves them a
  download. Take the **newest filename**, never the newest modified time.

Either way, run `scripts/open.py <url-or-path>`. It fetches, verifies the checksum,
refuses an archive whose names look encoding-damaged, refuses one that is not really a zip,
unpacks, runs `git fsck`, and commits any edits the user made outside a session. Each of
those failures is silent if skipped, which is why they are bundled rather than left as
steps to remember.

See `references/transport.md` for both routes in detail — single-use download URLs, what a
text-pasted archive looks like, and why the way out is always manual.

However it arrived, `open.py` handles unpacking, first-time `git init` when there is no
history, and committing edits made outside a session as 手動編輯 — that last one matters,
because work that is not committed is invisible to every later comparison and a
reconciliation would quietly discard it.

Then **orient**, in this order:
   - **最可能出事** — from `notes.md`. One sentence.
   - **等 and 不確定 lines** — what one message would unblock.
   - **What's due** — soonest first, briefly.
   - Anything notable since the last release, from `git log`.

Opening *is* the "上次到哪" habit — the command and the ritual are the same action, which
is why this works: it pays the user back the moment they run it.

**Nothing exists yet?** Create the skeleton — `todo.txt`, `notes.md`, `git init`, one
commit — and release it immediately so the user has something to file.

## Inside a project

A project is one cloud folder holding its releases, plus anything too heavy to travel:

```
2026-09-13_病歷學會AI課/          ← keeps its existing name; never rename it
  2026-08-18-1341_emr-ai-course.zip     ← current
  2026-08-18-1340_emr-ai-course.zip
  2026-08-15-0920_emr-ai-course.zip
  影片素材/                              ← too big to ride along, stays put
```

The zip name uses an ASCII slug, which is what travels; the folder keeps the name its
owner chose. `notes.md` inside records the folder path, so the two stay connected without
a mapping table.

**The archive root is the slug alone — no date.** The cloud folder carries the event date
so the drive sorts as a calendar; repeating it inside produces
`2026-08-18-1416_2026-09-13_emr-ai-course.zip`, two dates and three underscores, and the
single-underscore delimiter stops being readable. One date per name: the stamp in the
filename, the event in the folder.

Inside the zip:

```
todo.txt        what's next
done.txt        what happened
notes.md        three lines, written in the user's language
files/          documents
.git/           history — must always travel with the zip
```

Structural names are ASCII on purpose — see the section above. `notes.md` carries the
cloud folder it came from, so later opens need no reminder:

```
folder: /2026-09-13_病歷學會AI課
現在狀態：兩堂大綱還沒動
最可能出事：講題細節沒跟主辦確認就開始備課
在等誰：長庚十院窗口
```

Keep the slug stable once chosen — later releases reuse it, and sorting holds regardless
because the stamp leads.

A line has no syntax at all. **There is only one project, so nothing needs tagging:**

```
2026-08-18 兩堂大綱與講義草稿
2026-08-18 等長庚十院回覆開講時間
2026-08-18 不確定 WCIM 註冊繳費完成沒
```

Two words carry meaning, and they are words rather than symbols because a person reads
this and no program does: **等** means blocked on someone else, **不確定** means it may
already be done and there is no record either way. Never require them — someone writing
plainly is writing correctly. Group and name the categories yourself when reporting
("兩件在等別人，一件不確定做了沒"); the user learns no syntax and hears the
classification every time.

Finished and abandoned lines both move to `done.txt`, abandoned ones saying why in plain
words (`算了：重複`).

`notes.md` is three lines and no more:

```
現在狀態：兩堂大綱還沒動
最可能出事：講題細節沒跟主辦確認就開始備課
在等誰：無
```

The middle line is the whole difference between a task list and project management, and
it is what opening reads first.

## Committing

Commit as work happens — it is free here, with no round trip. Write the message about the
decision, not the file change: 「確認長庚時間 09:00，備課可以動了」 beats 「update
todo.txt」. Those messages are the project's history, and `git log` is what makes "上次到
哪" answerable beyond the current three lines.

Never rebase, never amend, never force. History is a record, and rewriting it destroys
the only thing that survives the round trip intact.

## Releasing

Run `scripts/release.py <project-dir>`. It commits anything outstanding, **tags the
released commit**, packs the whole directory **including `.git`**, then verifies the
archive reopens with its history and tag intact.

The tag *is* the filename prefix — tag `2026-08-18-1341` inside
`2026-08-18-1341_病歷學會AI課.zip` — so the archive and the history point at each other.
When two versions later diverge, the tags show which release each grew from instead of
having to be matched up by guesswork.

Hand it over under exactly the name it should have in the folder. The user's one manual
step is then a drag from Downloads into the project folder: nothing to rename, nothing to
choose, nothing to replace. An action that requires no decision is one that actually gets
done.

Then `present_files` it and say, in one line: put it in the project folder — **don't
replace anything**.

**Releases go back by hand.** No connector can write the zip back — this is a property of
the file APIs exposed to assistants, not one platform's gap. Pulling can be automatic;
pushing is the user's one manual step. Do not promise otherwise. `references/transport.md`
has the detail, including how to notice on the next open that a release never made it
back.

Release early and often, not just at the end. There is no end-of-conversation hook to
wait for, and a user who leaves mid-conversation should still have something to file.
Skip it only when nothing changed.

**`.git` must be in every zip.** Without it there is no shared history, and two versions
can only be diffed as loose text — no merge base, so no way to tell an added line from a
line the other side deleted. This is the one unrecoverable mistake.

**Heavy media cannot ride along.** Video, large datasets, big binaries — leave them in the
cloud folder and let the zip carry the text workspace. Say so when a project has them
rather than producing a zip too large to move.

## Two versions

Two releases both holding work — usually a machine at the office and one at home.

**Do not take the newer one.** "Which is newer" has no answer in a real fork: both sides
hold work the other lacks, and choosing one discards something real. Only when one side's
history contains the other is it safe to take the descendant.

Read `references/merging.md` and follow it whenever two zips of the same project turn up,
or when a fetch finds two releases with close timestamps.

## Reference files

- `references/transport.md` — how a project gets in and out: direct upload, connector
  fetch, and why releasing is always manual.
- `references/merging.md` — reconciling two versions that both hold work. Read it when
  two zips turn up, not before.
- `scripts/open.py` — fetching, verifying, unpacking, and capturing manual edits.
- `scripts/release.py` — packing, tagging, and verification. Always use it; never
  hand-roll the archive.

## Closing a project

When the work is done, unpack it into plain files in the cloud folder and retire the zip.
A zip is right while a project is live and being worked through conversation; it is wrong
for long-term storage, because nobody can open a phone and read what is inside it.

## What this deliberately does not do

One project, one conversation. Questions spanning every project at once — which case is
most at risk this week, what is blocked everywhere — need every zip open, so they belong
somewhere else: a separate overview file kept outside the zips, readable without
unpacking anything.

Two people cannot work this way. Both would produce zips claiming to be current, and
reconciling them by hand is the whole cost the fork procedure above exists to contain.
Say this before setting up, not after the first collision.
