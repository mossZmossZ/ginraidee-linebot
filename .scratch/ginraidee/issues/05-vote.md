# 05 — Cast and change one vote per person

**Phase:** P2
**Status:** Todo
**Blocked by:** [04 — Start or reuse a restaurant selection](04-start-selection.md)
**Owner:** Unassigned; requested developer/tester models remain pending confirmation
**Developer/tester rounds used:** 0 / 3

## What to build

Group members vote with the two buttons; changing a choice replaces their vote, and repeated taps do not increase their voting power.

## Todo

- [ ] Bind action data to the originating group, poll and choice.
- [ ] Persist unique user/poll votes with transactional updates.
- [ ] Enforce the deadline on every vote, independent of scheduler progress.
- [ ] Handle duplicate, stale and out-of-order events according to reviewed rules.

## Acceptance criteria

- [ ] Two users can vote and each has exactly one current vote per poll.
- [ ] Selecting the other restaurant replaces the previous choice; tapping the same button again adds no vote.
- [ ] Concurrent actions and duplicate webhooks cannot create multiple votes for a person.
- [ ] Actions from another group or another poll cannot change this poll.
- [ ] Missing usable voter identity is handled explicitly without counting anonymous duplicates.
- [ ] A vote at or after noon cannot change the result, even when the closure task is delayed.
- [ ] Old buttons do not reopen polls or mutate another day's votes.

## Verification

Signed postback flows, SQLite uniqueness/concurrency, changed votes, copied actions, duplicate event IDs and exact deadline boundaries.

Manual check: Two people cast and change votes and tap repeatedly in a real LINE group; review stored totals.

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
[board](../../../docs/kanban.md). Criteria depending on proposed D1–D7 rules
must follow the decisions recorded in card 00.

