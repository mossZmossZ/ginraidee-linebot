# 11 — Rich-menu setup forms and optional restaurant images

**Phase:** P1 amendment
**Status:** Todo
**Blocked by:** [02 — Add/view restaurants](02-add-restaurants.md); [03 — Edit/delete restaurants](03-edit-delete.md)
**Owner:** Developer when the card is Ready
**Developer/tester rounds used:** 0 / 3

## What to build

Project-owner amendment on 2026-10-16: `@ginraidee-bot manage` opens a group
menu card linking to a setup form. A native rich menu in the bot's private chat
opens the same UI. The owner explicitly selected both entry points. Restaurant
input uses forms rather than chat Q&A; a name is required and images are optional.

## Todo

- [ ] Add group menu-card and private-chat rich-menu entry points, retaining command aliases.
- [ ] Serve the shared Thai List/Add/Edit/Delete form and API from FastAPI.
- [ ] Configure LIFF/LINE Login under the bot's provider and verify tokens on the server.
- [ ] Bind setup access to webhook-derived group context and verified user; check current membership, deny unverifiable access, expire after 10 inactive minutes, and reject copied/forged grants.
- [ ] Let private-menu users choose only verified group contexts; explain how to run manage when none exists. Provide a desktop setup link because native rich menus are unavailable there.
- [ ] Require a nonblank unique name; validate only supplied HTTPS image URLs, and support preserving, replacing, or explicitly removing an image.
- [ ] Migrate image columns to permit absence while preserving catalog rows, existing URLs, and poll snapshots; render name-only entries without image components.
- [ ] Keep Cancel, delete confirmation, row-version checks, safe double submissions, and group isolation; stop consuming chat replies as restaurant input.
- [ ] Document static rich-menu artwork separately from optional restaurant photos, LIFF configuration, deployment, and updated manual checks.

## Acceptance criteria

- [ ] Both entry points open the same group-scoped setup UI; management never creates a poll.
- [ ] Any verified group member can add/view/edit/delete through forms without typing names, numbers, URLs, or confirmations as chat replies.
- [ ] Add succeeds with a name only; an edit can preserve, replace, or remove its image. Invalid supplied URLs and duplicate/blank names leave saved data unchanged.
- [ ] Name-only and mixed-image entries work in catalogs, sole-restaurant selections, votes, and final results, with valid LINE payloads.
- [ ] Migration preserves existing records/URLs and snapshot image presence or absence; catalog edits do not alter active polls.
- [ ] Cancel and expired sessions do not write; stale forms cannot edit/delete the wrong record; duplicate Save requests do not duplicate changes.
- [ ] Server-verified identity, group membership, and bound setup grants prevent foreign-group access and copied-link abuse; no raw group ID is trusted for authorization.
- [ ] Private rich-menu access selects only authorized groups; mobile entry points and desktop fallback are documented and manually checked.

## Verification

Focused integration checks for menu dispatch, authenticated form CRUD,
nullable-image migration/rendering, cancellation/expiry, stale versions,
double submissions, and copied/foreign setup links. Recheck selection/result
integration when Cards 04–06 are available before release.

Manual check: Two users in two groups open setup from the group card and private
rich menu, manage name-only and imaged entries, remove an image, cancel and
confirm deletion, and verify desktop access and group isolation (U03–U06,
U16–U19, U25–U27).

## Evidence and handoff

Planning only. Existing Card 02–03 evidence covers the prior chat flow and
does not verify this amendment. This card is required by production Card 07;
Card 08 verifies integration with selection and results. Existing round counts
and outstanding manual checks remain unchanged.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| — | Not started | Not run | — |

Tech-lead review: Not recorded.
CEO/manual disposition: Scope and both entry points confirmed on 2026-10-16; implementation/UAT not run.
Linked bugs / continuation: None recorded.

See the [implementation plan](../../../docs/implementation-plan.md),
[workflow](../../../docs/development-workflow.md), and [board](../../../docs/kanban.md).
