# Reconciling two versions

Read this when two releases of the same project both hold work — usually a machine at
the office and one at home. It is rare, and you will know when it happens: two zips are
in front of you.

Divergence looks like two zips, usually a machine at work and one at home.

**"Which is newer" is the wrong question**, and in the case that matters it has no answer.
If one side's history contains the other's, it is not really a conflict — take the
descendant. A real conflict is a *fork*: both sides hold work the other lacks, and
choosing one discards something real.

What git actually gives you is better. Unpack both, commit any uncommitted edits on each
side, then find the merge base and show what each side added since they split.

**Resolve mechanically wherever possible, and it usually is.** These files are
line-oriented and most edits are additions:

- Lines added on either side → keep both.
- Identical or duplicated lines → collapse.
- One side deleted, the other untouched → honour the deletion.

**Ask only where the same line says two different things about reality** — "WCIM 註冊已完成"
against "WCIM 註冊還沒繳費". Git can prove the two sides disagree; it cannot know which is
true. Only the user does, and guessing there is guessing about their world — wrong
silently, and believed afterwards. That is usually one or two lines out of twenty.

Release the merged result as a new zip, same as any other release.

## Doing it

Unpack both under different names, then commit any uncommitted edits on each side —
work that is not committed is invisible to every comparison below, and would be silently
discarded.

```bash
cd A && git status --porcelain && git add -A && git commit -qm "手動編輯"
```

Bring one into the other as a remote and find where they split:

```bash
cd A
git remote add other ../B && git fetch -q other
git merge-base HEAD other/master        # the shared starting point
git log --oneline HEAD...other/master   # what each side has that the other lacks
```

The release tags make this legible: each side carries the tag of the release it grew
from, so `git tag --merged` on either side names the last release they had in common.

For the text files, attempt the merge and let git resolve what it can:

```bash
git merge other/master
```

Additions on both sides merge cleanly and need no decision. What remains in conflict is
the same line saying two different things — that is the part to bring to the user, quoted
plainly, one question per genuine disagreement.

If the histories turn out to be unrelated — someone re-ran `git init`, or a round trip
lost `.git` — there is no merge base and none of this applies. Say so, and fall back to
showing the two files side by side and asking. Do not fabricate a shared history with
`--allow-unrelated-histories`; it produces a merge that looks authoritative and is not.

Release the result as an ordinary release. The merge commit records both parents, so the
fork is visible in history afterwards rather than being smoothed over.
