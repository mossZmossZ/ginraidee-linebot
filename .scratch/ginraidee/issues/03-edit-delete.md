# 03 — Edit and delete restaurants in the group

**Phase:** P1
**Status:** Todo
**Blocked by:** [02 — Add and view group restaurants with HTTPS image URLs](02-add-restaurants.md)
**Owner:** Separate `terra`, high chat when the card is Ready
**Developer/tester rounds used:** 0 / 3

## What to build

Any member edits a selected restaurant's name/image or confirms its deletion through @ginrai-manage.

## Todo

- [ ] Add clear entry selection for Edit and Delete.
- [ ] Implement validated edits and accepted deletion-confirmation behavior.
- [ ] Handle concurrent changes and canceled/expired sessions safely.
- [ ] Preserve image URLs according to accepted retention/snapshot decisions.

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

