#!/usr/bin/env python3
"""Tests for the todo.txt-spec exporter. Stdlib only; run: python3 tests/test_todotxt.py

Expected values come from the todo.txt spec, not from running the code — a completed line
is `x <date> ...`, a leading YYYY-MM-DD is the creation date, contexts are @word.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "init" / "scripts"))
import todotxt  # noqa: E402

T = "2026-09-15"
passed = failed = 0


def eq(got, want, label):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"  FAIL {label}\n    want: {want!r}\n    got:  {got!r}")


# --- done lines: completion mark, dates, idempotency, CJK preserved ---
eq(todotxt.to_spec_done("算了：重複", T), "x 2026-09-15 算了：重複", "done: plain abandoned")
eq(todotxt.to_spec_done("兩堂大綱與講義草稿", T), "x 2026-09-15 兩堂大綱與講義草稿", "done: plain finished")
eq(todotxt.to_spec_done("2026-08-18 兩堂大綱", T), "x 2026-09-15 2026-08-18 兩堂大綱",
   "done: creation date preserved as second date")
eq(todotxt.to_spec_done("x 2026-09-15 算了：重複", T), "x 2026-09-15 算了：重複",
   "done: idempotent — already completed")
eq(todotxt.to_spec_done(todotxt.to_spec_done("算了：重複", T), T),
   "x 2026-09-15 算了：重複", "done: double-apply stable")
eq(todotxt.to_spec_done("", T), "", "done: blank line preserved")

# --- todo lines: waiting / uncertain contexts, creation date, idempotency ---
eq(todotxt.to_spec_todo("2026-08-18 兩堂大綱與講義草稿"), "2026-08-18 兩堂大綱與講義草稿",
   "todo: plain, creation date kept, no tag")
eq(todotxt.to_spec_todo("2026-08-18 等長庚十院回覆開講時間"),
   "2026-08-18 等長庚十院回覆開講時間 @waiting", "todo: 等 → @waiting")
eq(todotxt.to_spec_todo("2026-08-18 不確定 WCIM 註冊繳費完成沒"),
   "2026-08-18 不確定 WCIM 註冊繳費完成沒 @uncertain", "todo: 不確定 → @uncertain")
eq(todotxt.to_spec_todo("等長庚回覆"), "等長庚回覆 @waiting", "todo: 等 with no date")
eq(todotxt.to_spec_todo(todotxt.to_spec_todo("2026-08-18 等長庚回覆")),
   "2026-08-18 等長庚回覆 @waiting", "todo: idempotent — no double @waiting")
eq(todotxt.to_spec_todo(""), "", "todo: blank line preserved")

# --- file-level export: writes export/, source untouched, idempotent, CJK intact ---
with tempfile.TemporaryDirectory() as d:
    proj = Path(d)
    todo_src = "2026-08-18 等長庚十院回覆開講時間\n2026-08-18 不確定 WCIM 繳費了沒\n"
    done_src = "算了：重複\n2026-08-01 場地確認\n"
    (proj / "todo.txt").write_text(todo_src, encoding="utf-8")
    (proj / "done.txt").write_text(done_src, encoding="utf-8")

    written = todotxt.export(proj, T)
    eq(sorted(written), ["export/done.txt", "export/todo.txt"], "export: both files written")

    # source files must be byte-for-byte untouched
    eq((proj / "todo.txt").read_text(encoding="utf-8"), todo_src, "export: source todo untouched")
    eq((proj / "done.txt").read_text(encoding="utf-8"), done_src, "export: source done untouched")

    spec_todo = (proj / "export" / "todo.txt").read_text(encoding="utf-8")
    eq(spec_todo,
       "2026-08-18 等長庚十院回覆開講時間 @waiting\n2026-08-18 不確定 WCIM 繳費了沒 @uncertain\n",
       "export: todo spec content")
    spec_done = (proj / "export" / "done.txt").read_text(encoding="utf-8")
    eq(spec_done, "x 2026-09-15 算了：重複\nx 2026-09-15 2026-08-01 場地確認\n",
       "export: done spec content")

    # re-export is stable (idempotent at the file level too)
    todotxt.export(proj, T)
    eq((proj / "export" / "done.txt").read_text(encoding="utf-8"), spec_done,
       "export: re-run idempotent")

# --- export with no source files is a safe no-op ---
with tempfile.TemporaryDirectory() as d:
    eq(todotxt.export(Path(d), T), [], "export: no source → no-op")

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
