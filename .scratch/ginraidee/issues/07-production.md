# 07 — Run and recover the standalone production deployment

**Phase:** P4
**Status:** Todo
**Blocked by:** [03 — Edit and delete restaurants in the group](03-edit-delete.md); [06 — Close at noon and recover stable results](06-close-polls.md)
**Owner:** Separate `terra`, high chat when the card is Ready
**Developer/tester rounds used:** 0 / 3

## What to build

An operator starts the full bot using only docker-compose-prod.yml and runtime configuration, with public HTTPS, persistent data and a verified recovery procedure.

## Todo

- [ ] Create the standalone server Compose configuration and safe container runtime settings.
- [ ] Configure the agreed public HTTPS webhook/image endpoint and health checks.
- [ ] Document and verify single-worker/closer deployment constraints and startup recovery.
- [ ] Add a consistent SQLite-plus-images backup/restore procedure.

## Acceptance criteria

- [ ] The production Compose configuration runs independently of the development Compose file.
- [ ] Configured public HTTPS webhook and image URLs work from outside the server.
- [ ] Database and images survive app container replacement and ordinary restart.
- [ ] Only intended public routes are exposed; runtime secrets stay outside the image/repo.
- [ ] A backup restores consistent restaurant records, polls/votes and referenced images in an isolated deployment.
- [ ] Restart recovers due polls and pending result delivery without changing winners.
- [ ] Normal operator instructions do not delete persistent volumes.

## Verification

Validate both Compose files, fresh production startup, public endpoint smoke checks, container replacement and isolated backup/restore.

Manual check: Operator follows server setup from scratch on the agreed target, recreates the app and restores a test backup.

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

