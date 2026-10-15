# 02 — Add and view group restaurants with persistent images

**Phase:** P1
**Status:** Todo
**Blocked by:** [01 — Run a local bot that safely receives group commands](01-local-bot.md)
**Owner:** Unassigned; requested developer/tester models remain pending confirmation
**Developer/tester rounds used:** 0 / 3

## What to build

Any group member adds a restaurant through the guided chat flow and sees its name and backend-hosted image in that group's list.

## Todo

- [ ] Implement guided Add and list/preview interactions with per-user/group sessions.
- [ ] Fetch and validate supplied HTTPS image URLs with bounded safe network access.
- [ ] Store image files and restaurant records consistently on persistent storage.
- [ ] Serve only validated image files through the public image endpoint.

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

