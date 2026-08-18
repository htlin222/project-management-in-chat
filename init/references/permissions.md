# Connector permissions

Read this when a connector is involved and something fails, when deciding whether a
connector is worth setting up, or when the user asks what access is needed.

A connector is never required. A zip dragged into the conversation works with no cloud
access at all. Everything here is about the optional convenience of fetching.

## What each level of access buys

| Access | Fetching a project | Releasing it back |
|---|---|---|
| No connector | User downloads and uploads the file | Manual |
| Read-only | **Automatic** — list, find newest, download | Manual |
| Read + create | Automatic | **Still manual** |
| Full write | Automatic | **Still manual** |

The last two rows are the ones people get wrong.

**More permission does not make releasing automatic.** The ceiling is not the permission
level, it is the tool surface: the file-creation tools exposed by these connectors accept
**text content only** and explicitly refuse binary. A zip is binary. Granting write access
changes nothing about the return trip.

This matters practically, because someone will ask IT to broaden access expecting the loop
to close, and it will not. Say so before they file the request. Read-only is genuinely
enough for everything a connector contributes here.

## Establish what you have — do not assume

Permission varies by tenant, by site, and sometimes by folder. Discovering it through a
failure halfway through a task is worse than checking first:

1. **List the project folder.** Success means read access reaches this location, which is
   all that fetching needs.
2. **Request a download link for one file.** Listing can succeed where content access is
   blocked; these are separate permissions on some platforms.
3. **Stop there.** Do not test write access by creating files in the user's storage.

If a connector is not connected at all, say so plainly and fall back to direct upload
rather than walking the user through setup mid-task. Setting one up saves a download, not
a step — the upload half stays manual regardless.

## Reading failures correctly

These look alike and mean different things. Naming the right one saves the user a wasted
conversation with IT.

**Not found, on a folder the user says exists.** Usually the folder is outside the
connector's granted scope rather than misspelled — many enterprise deployments scope
access to specific sites, drives, or folders. Confirm the exact path with the user, and if
it is right, report it as a scope limitation.

**Forbidden.** The connection is valid but this location is not permitted. Name the
location; do not retry, and do not fall back to something that looks like it worked.

**Expired or consumed download link.** Temporary download URLs are typically single-use
and are consumed by the first request of any method, including HEAD. Request a fresh link
rather than reusing one.

**Listing works, download fails.** Metadata and content are separate permissions on some
platforms. Report it that way rather than as a general access problem.

Never route around a missing permission — no guessing at paths, no alternative endpoints,
no fetching the same file by another means. Report what is missing and let the user decide
whether to ask for it.

## Shared locations

A shared folder is fine for holding releases: everyone can see progress and download.
**Only one person should upload**, because two people releasing produces two archives each
claiming to be current, and in a shared folder everyone assumes someone else is handling
it. Reconciliation exists (`merging.md`) but it is recovery, not a workflow.

This tends to match how organisations already work — a document has an owner, everyone
else reviews.

## Enterprise realities worth stating up front

- **Read-only is often deliberate.** It is a security decision, not a misconfiguration, and
  it will not change because a task would be more convenient. Design around it.
- **The connector may be scoped to particular sites or drives.** Personal storage may be
  reachable while a department site is not, or the reverse.
- **Policy may forbid connecting cloud storage to an assistant entirely.** Direct upload
  still works, and nothing in this skill depends on a connector.
- **What can be discussed at all may be narrower than what can be accessed.** Access
  permission is not the same as permission to put the content into a conversation. If
  material looks regulated or identifiable, raise it rather than proceeding because the
  connector allowed the read.
