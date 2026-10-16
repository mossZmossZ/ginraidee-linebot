# 02 — Add and view group restaurants with HTTPS image URLs

**Phase:** P1
**Status:** In development
**Blocked by:** [01 — Run a local bot that safely receives group commands](01-local-bot.md)
**Owner:** Current Codex workspace
**Developer/tester rounds used:** 1 / 3

## What to build

Any group member adds a restaurant through the guided chat flow and sees its name and original HTTPS image URL in that group's list.

## Todo

- [x] Implement guided Add and list/preview interactions with per-user/group sessions.
- [x] Validate and retain supplied HTTPS image URLs without downloading them.
- [x] Store restaurant records and original image URLs consistently in SQLite.
- [x] Send original HTTPS image URLs directly to LINE in catalog previews.

## Acceptance criteria

- [ ] A group member can provide a nonblank restaurant name and HTTPS image URL and see the saved entry.
- [ ] Other members of that group can see the entry; another group cannot see or change it.
- [ ] Original HTTPS image URLs are retained after application container replacement and sent directly to LINE.
- [ ] Invalid or non-HTTPS URLs do not create a partial entry.
- [ ] Canceled/expired sessions and simultaneous users behave according to accepted D3 rules.

## Verification

Guided webhook flow with HTTPS image URLs, independent group/user sessions, URL validation, and container replacement persistence.

Manual check: Two members add restaurants in a real group, view the images, and verify a second group stays separate.

## Evidence and handoff

Developer environment: current Codex workspace, Python 3.12.13 via `uv`.

Implemented the Thai guided Add/List flow, scoped management sessions, retained
original HTTPS image URLs in SQLite, direct LINE image messages, and per-group
normalized-name uniqueness.

Focused checks run:

- `uv run --group dev pytest -q` — 16 passed (one upstream Starlette deprecation warning).
- `uv run --group dev ruff check .` — passed.
- `docker compose config` with placeholder credentials — passed.
- `docker compose build` — passed; the resulting image does not install Pillow.

Manual check: not run; requires two real group members, a configured public HTTPS
endpoint, and the project owner's LINE credentials.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| 1 | Guided flow, malformed/HTTP URL rejection, paginated catalog previews, SQLite URL storage, direct LINE image messages, and durable receipts implemented; automated checks recorded above | Not run | Await independent tester verification and required real LINE check. |

Tech-lead review: Not recorded.
CEO/manual disposition: Not recorded.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules
must follow the decisions recorded in card 00.

