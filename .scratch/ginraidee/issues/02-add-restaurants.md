# 02 — Add and view group restaurants with persistent images

**Phase:** P1
**Status:** In development
**Blocked by:** [01 — Run a local bot that safely receives group commands](01-local-bot.md)
**Owner:** Current Codex workspace
**Developer/tester rounds used:** 1 / 3

## What to build

Any group member adds a restaurant through the guided chat flow and sees its name and backend-hosted image in that group's list.

## Todo

- [x] Implement guided Add and list/preview interactions with per-user/group sessions.
- [x] Fetch and validate supplied HTTPS image URLs with bounded safe network access.
- [x] Store image files and restaurant records consistently on persistent storage.
- [x] Serve only validated image files through the public image endpoint.

## Acceptance criteria

- [ ] A group member can provide a nonblank restaurant name and HTTPS image URL and see the saved entry.
- [ ] Other members of that group can see the entry; another group cannot see or change it.
- [ ] Downloaded images are served from the backend and remain available after application container replacement.
- [ ] Validation failures, oversized content, private/local destinations and unsafe redirect chains do not create a partial entry or unsafe file.
- [ ] Canceled/expired sessions and simultaneous users behave according to accepted D3 rules.
- [ ] The database file and unrelated files cannot be retrieved through image serving.

## Verification

Guided webhook flow with fake image responses, independent group/user sessions, URL/redirect validation and container replacement persistence.

Manual check: Two members add restaurants in a real group, view the images, and verify a second group stays separate.

## Evidence and handoff

Developer environment: current Codex workspace, Python 3.12.13 via `uv`.

Implemented the Thai guided Add/List flow, scoped management sessions, normalized
backend-hosted PNG files, opaque image serving, HTTPS-only image retrieval with
DNS/redirect/private-address checks, and per-group normalized-name uniqueness.

Focused checks run:

- `uv run --group dev pytest -q` — 19 passed.
- `uv run --group dev ruff check .` — passed.
- Isolated Docker Compose smoke check — image built; container became healthy;
  `/data/ginraidee.db` remained present after `docker compose restart bot`.
  The temporary container and network were stopped; its named volume was kept.

Manual check: not run; requires two real group members, a configured public HTTPS
endpoint, and the project owner's LINE credentials.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| 1 | Guided flow, image-safety controls, storage, endpoint, durable receipts, and recoverable orphan handling implemented; checks recorded above | Not run | Await independent tester verification and required real LINE check. |

Tech-lead review: Not recorded.
CEO/manual disposition: Not recorded.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules
must follow the decisions recorded in card 00.

