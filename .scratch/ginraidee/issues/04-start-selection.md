# 04 — Start or reuse a restaurant selection

**Phase:** P2
**Status:** Todo
**Blocked by:** [02 — Add and view group restaurants with HTTPS image URLs](02-add-restaurants.md)
**Owner:** Separate `terra`, high chat when the card is Ready
**Developer/tester rounds used:** 0 / 3

## What to build

Before noon, @ginraidee-bot selects two distinct eligible restaurants and opens a custom vote, or directly announces a sole restaurant.

## Todo

- [ ] Implement Bangkok lunch-date/deadline calculations with an injectable clock.
- [ ] Select uniformly without replacement and save immutable choices.
- [ ] Render voting buttons and reuse the existing open poll.
- [ ] Render name-only and mixed-image choices; omit image components when absent (D9/Card 11).
- [ ] Implement accepted empty-list, daily-selection and post-noon rules.

## Acceptance criteria

- [ ] Only the typed @ginraidee-bot command starts a selection; ordinary conversation and schedules do not.
- [ ] With at least two entries, exactly two distinct choices come from that group's catalog with no weighting.
- [ ] With one entry, announce it directly, explain only one is available and do not open a vote.
- [ ] Repeating/concurrently sending @ginraidee-bot reuses the same open choices without resetting votes or deadline.
- [ ] At or after 12:00 Asia/Bangkok, show today's result or the closed message; never open a new poll.
- [ ] Empty catalogs, repeated days and single-restaurant daily results follow accepted D1.
- [ ] Choice names/images remain stable independently of later catalog updates.
- [ ] Missing images never block selection; snapshots preserve absence, and name-only choices/results have valid LINE payloads.

## Verification

Zero/one/two/many entry cases, concurrent start transactions, fake-clock noon/date boundaries and deterministic sampling-contract tests.

Manual check: Start and repeat selections in two groups, including a one-restaurant group; check displayed choices and deadlines.

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

