# 06 — Close at noon and recover stable results

**Phase:** P3
**Status:** Todo
**Blocked by:** [05 — Cast and change one vote per person](05-vote.md)
**Owner:** Separate `terra`, high chat when the card is Ready
**Developer/tester rounds used:** 0 / 3

## What to build

Started polls close at Bangkok noon, store the correct winner/fallback reason, and publish results according to the accepted announcement policy.

## Todo

- [ ] Persist due times and close due polls transactionally.
- [ ] Resolve majority, tie and no-vote outcomes once and store the reason.
- [ ] Add durable outgoing result work, bounded retries and delivery failure visibility.
- [ ] Recover overdue polls and interrupted delivery after restart.

## Acceptance criteria

- [ ] A started poll stops accepting votes at 12:00 Asia/Bangkok without needing a fresh user command.
- [ ] A clear majority wins; ties and no votes choose only between the saved choices and explain the fallback.
- [ ] The winner is stored once and is not re-randomized after duplicate work, retries or restart.
- [ ] On restart after noon, overdue polls close and accepted announcement work resumes.
- [ ] Failed/limited LINE delivery does not reopen voting; retries and unresolved delivery failures are visible.
- [ ] No new poll is created by the closer; no active poll means no scheduled lunch announcement.
- [ ] @ginraidee-bot after closure returns the same stored result; old reply tokens are not reused for noon push delivery.

## Verification

Controlled-clock majority/tie/no-vote cases, close-vote races, crash/restart, stable outcome persistence and simulated outgoing failures.

Manual check: Verify noon closure and result text in a real group, then review a controlled interrupted-delivery/restart demonstration.

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

