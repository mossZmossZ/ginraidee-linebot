# 02 — Add and view group restaurants with HTTPS image URLs

**Phase:** P1
**Status:** In development
**Blocked by:** [01 — Run a local bot that safely receives group commands](01-local-bot.md)
**Owner:** Current Codex workspace
**Developer/tester rounds used:** 1 / 3

Scope amendment, 2026-10-16: the target now uses menu/form setup with optional
images. [Card 11](11-management-setup.md) replaces the implemented guided chat
UI and migrates images to optional values. The checked tasks and evidence
below record the earlier implementation; they do not verify the new behavior.
Card 11 is required before production acceptance, alongside the checks here.

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

Tech-lead automated spot-check on 2026-10-16 at revision `eb195cc`:

- `UV_CACHE_DIR=/private/tmp/ginraidee-uv-cache uv run --offline --group dev pytest -q tests/test_catalog.py tests/test_webhook.py` — 23 passed (one upstream Starlette deprecation warning).
- `UV_CACHE_DIR=/private/tmp/ginraidee-uv-cache uv run --offline --group dev ruff check .` — passed.

Container-replacement check on 2026-10-16 at revision `eb195cc`: built the app
image and used isolated Compose project `ginraidee-card02-verify-28996` with
placeholder LINE credentials. Seeded one restaurant and its HTTPS image URL
into the named volume, removed the app container, then started a replacement
container using the same volume. The app health check passed before and after;
the restaurant name and original URL remained in SQLite. The temporary
containers, network, and volume were removed. No LINE API call was made.

These local checks are not the separate tester verification required by the
workflow and do not verify real LINE behavior. The project owner separately
reported that real LINE testing was complete and signed off in Codex chat on
2026-10-16; specific test details were not included.

Manual check: the project owner reported that real LINE testing was already
complete and gave signoff in Codex chat on 2026-10-16. Specific participants,
scenarios, and observations were not included in the message.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| 1 | Guided flow, malformed/HTTP URL rejection, paginated catalog previews, SQLite URL storage, direct LINE image messages, and durable receipts implemented; automated checks recorded above | Not run | Await independent tester verification. Project owner reports real LINE testing complete and signed off; detailed evidence was not supplied. |

Tech-lead review: Automated checks and isolated container-replacement check
recorded above; formal review after independent tester verification remains
pending.
CEO/manual disposition: Project owner provided signoff in Codex chat on
2026-10-16 and reported that testing was already complete; detailed results
were not supplied.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules
must follow the decisions recorded in card 00.

