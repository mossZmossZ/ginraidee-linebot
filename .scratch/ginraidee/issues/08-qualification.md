# 08 — Qualify isolation, concurrency and failure recovery

**Phase:** P4
**Status:** Todo
**Blocked by:** [07 — Run and recover the standalone production deployment](07-production.md)
**Owner:** Separate `terra`, high chat when the card is Ready
**Developer/tester rounds used:** 0 / 3

## What to build

The complete deployed candidate preserves correct group behavior under simultaneous commands, hostile/broken images, duplicate events and interrupted processing.

## Todo

- [ ] Exercise cross-feature scenarios with two groups and overlapping management sessions.
- [ ] Verify concurrent starts/votes, webhook deduplication and out-of-order rules.
- [ ] Inject crashes and image/LINE failures; verify durable work recovery.
- [ ] Fix findings only within the developer/tester round limit and record remaining defects.

## Acceptance criteria

- [ ] Group A cannot read/mutate Group B's catalog, sessions, poll choices or votes through copied action data.
- [ ] Repeated event delivery does not duplicate saves, polls, votes or logical closing outcomes.
- [ ] Crash after webhook acceptance does not silently lose acknowledged durable work.
- [ ] Image destination/redirect protections and file-serving boundaries hold in the deployed candidate.
- [ ] Catalog edits during polls and image retention follow reviewed policies without broken snapshots.
- [ ] Delivery failures, due-poll recovery and exact noon boundaries pass meaningful regression checks.
- [ ] Findings include reproduction and evidence; any third-round failure becomes Pending with a linked Bug.

## Verification

Integration and targeted fault-injection suite; repeat checks only when fixes or unresolved findings justify them.

Manual check: Tester demonstrates the highest-impact isolation and recovery cases and submits evidence to tech lead/CEO.

## Evidence and handoff

No implementation or verification evidence yet.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| — | Not started | Not run | — |

Tech-lead review: Not recorded.
CEO/manual disposition: Not recorded.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules
must follow the decisions recorded in card 00.

