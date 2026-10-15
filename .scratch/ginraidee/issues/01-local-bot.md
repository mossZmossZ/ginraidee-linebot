# 01 — Run a local bot that safely receives group commands

**Phase:** P1
**Status:** Todo
**Blocked by:** [00 — Review the implementation plan and operating decisions](00-review-plan.md)
**Owner:** Unassigned; requested developer/tester models remain pending confirmation
**Developer/tester rounds used:** 0 / 3

## What to build

An operator starts the Dockerized bot locally, and a signed LINE group command reaches the bot and receives an initial setup response.

## Todo

- [ ] Add the Python/FastAPI application, pinned dependencies and local Compose setup.
- [ ] Add configuration, health checking and SQLite initialization on persistent storage.
- [ ] Validate the raw-body webhook signature and route exact group commands.
- [ ] Add focused signed-webhook and container startup checks.

## Acceptance criteria

- [ ] Documented local startup reaches a healthy bot with persistent SQLite storage.
- [ ] A valid signed group @ginrai command reaches the command handler and, for an empty catalog, follows the accepted D1 setup behavior.
- [ ] @ginrai-manage reaches its own management entry point rather than starting a poll.
- [ ] Ordinary messages, unsupported chat sources and invalid signatures create no lunch-selection effects.
- [ ] Secrets are supplied through environment/configuration and are absent from committed files and logs.
- [ ] Restarting the app preserves initialized persistent state.

## Verification

Signed/invalid webhook fixtures, exact-command dispatch, temporary SQLite initialization and local Compose smoke check.

Manual check: Operator starts the local container and sends an initial command in a test LINE group through a configured HTTPS tunnel/endpoint.

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

