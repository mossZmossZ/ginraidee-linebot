# 03 — Edit and delete restaurants in the group

**Phase:** P1
**Status:** In development
**Blocked by:** [02 — Add and view group restaurants with HTTPS image URLs](02-add-restaurants.md)
**Owner:** Current Codex workspace, by project-owner direction
**Developer/tester rounds used:** 1 / 3

Project-owner direction on 2026-10-16 authorized Card 03 implementation to
start while Card 02 still awaits tester verification and manual LINE UAT. This
starts implementation only; it does not mark Card 02 Done or waive Card 03's
own review and manual acceptance.

## What to build

Any member edits a selected restaurant's name/image or confirms its deletion through @ginraidee-bot manage.

## Todo

- [x] Add clear entry selection for Edit and Delete using group-scoped restaurant numbers backed by non-reusable internal keys.
- [x] Implement validated edits and explicit deletion confirmation.
- [x] Handle concurrent changes with version checks; canceled and expired sessions do not mutate restaurants.
- [x] Preserve HTTPS image URLs and update records without changing any poll data.

## Acceptance criteria

- [ ] Any member can edit the intended restaurant or confirm deleting it.
- [ ] A changed HTTPS image URL is retained and sent directly to LINE using the same validation as Add.
- [ ] Cancel leaves the entry unchanged; a stale selection never edits/deletes the wrong entry.
- [ ] Another group's restaurant cannot be mutated by copied or forged action data.
- [ ] Changing/deleting a restaurant does not corrupt existing poll-choice snapshots under accepted D2.

## Verification

End-to-end management edit/delete fixtures, overlapping sessions, stale versions, group scoping and image URL checks.

Manual check: Two group members exercise Edit, Cancel and Delete, then verify the resulting catalog and images.

## Evidence and handoff

Developer environment: current Codex workspace, Python 3.12.13 via `uv`.

Added Edit/Delete management flows. Selection uses the restaurant number shown
in the group-scoped list. Each row also has a non-reusable internal key and
version, so a stale selection cannot mutate a changed row or a new row that
reuses a SQLite integer ID. Edits use the existing HTTPS URL validation, reject
blank and duplicate names, and send the updated source image URL to LINE.
Deletion requires `ยืนยัน`; `ยกเลิก` clears the session without changing the
restaurant. SQLite upgrades add row versions, selection keys, and session state
to existing databases without removing catalog data.

Focused checks run:

- `UV_CACHE_DIR=/private/tmp/ginraidee-uv-cache uv run --offline --group dev pytest -q` — 22 passed (one upstream Starlette deprecation warning).
- `UV_CACHE_DIR=/private/tmp/ginraidee-uv-cache uv run --offline --group dev ruff check .` — passed.

Manual check: not run; requires two real group members and the project owner's
LINE credentials.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| 1 | Edit/delete, confirmation/cancel, URL/name validation, group isolation, stale-version, reused-ID, and database migration scenarios implemented; automated checks recorded above | Not run | Await independent tester verification and required real LINE check. |

Tech-lead review: Not recorded.
CEO/manual disposition: Project owner authorized implementation to start before Card 02 verification on 2026-10-16; Card 03 manual UAT is not run.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules
must follow the decisions recorded in card 00.

