# 10 — Complete manual acceptance and release review

**Phase:** P5
**Status:** Todo
**Blocked by:** [08 — Qualify isolation, concurrency and failure recovery](08-qualification.md); [09 — Document fresh setup, contribution and operation](09-operator-docs.md)
**Owner:** Unassigned; requested developer/tester models remain pending confirmation
**Developer/tester rounds used:** 0 / 3

## What to build

Tester, tech lead and CEO have a concrete release report with real LINE group evidence, accepted behavior and explicit unresolved defects.

## Todo

- [ ] Run the manual UAT scenarios against the candidate revision.
- [ ] Collect tester results, automated check evidence and operating limitations.
- [ ] Review all Pending/Bug cards and their effect on scope/release.
- [ ] Record tech-lead recommendation and CEO disposition; update board/card statuses.

## Acceptance criteria

- [ ] Required UAT scenarios have actual results, environment/revision, tester identity and evidence.
- [ ] Manual results cover two users/groups, management, selection, changed votes, noon closure and persistence/recovery.
- [ ] No unrun/failed required check is marked Pass or Done.
- [ ] All held bugs show affected cards, rounds used, reproduction and continuation steps.
- [ ] Tech lead reports delivered behavior, evidence and risks to CEO.
- [ ] CEO's acceptance, reduced-scope decision or hold is recorded; a plan alone does not count as acceptance.
- [ ] Deployment/publication occurs only within the user's separately authorized release scope.

## Verification

Review final automated reports and manual UAT evidence; re-test fixes rather than duplicating implementation-only checks.

Manual check: Tech lead and CEO perform/review the final manual LINE checks with the assigned human tester and record the release decision.

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

