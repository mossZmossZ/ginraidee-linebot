# 09 — Document fresh setup, contribution and operation

**Phase:** P4
**Status:** Todo
**Blocked by:** [07 — Run and recover the standalone production deployment](07-production.md)
**Owner:** Unassigned; requested developer/tester models remain pending confirmation
**Developer/tester rounds used:** 0 / 3

## What to build

Another operator can obtain the repo, supply their own agreed configuration, run the bot and understand how to contribute and maintain it.

## Todo

- [ ] Write the local/server quickstarts and LINE account/group/webhook configuration steps.
- [ ] Document environment variables, image hosting, persistence, backups and delivery failures.
- [ ] Add contribution/test instructions and a CI check plan/configuration for the chosen tools.
- [ ] Record the accepted license/distribution policy and known limitations.

## Acceptance criteria

- [ ] A fresh operator can follow the appropriate local and production setup without hidden credentials or dependencies.
- [ ] Both required Compose filenames, volume behavior and public HTTPS requirements are documented correctly.
- [ ] Configuration examples contain placeholders only; no tokens, database files or downloaded user images are committed.
- [ ] Contributors can run the agreed focused test/lint/configuration checks using pinned dependencies.
- [ ] License text is added only after its selection; public release remains held while the license is undecided.
- [ ] Known limitations and Pending bugs are discoverable and not described as passing features.

## Verification

Fresh-setup walkthrough, documentation/command link checks and execution of documented checks once implementation exists.

Manual check: A reviewer follows the instructions from a clean checkout and records corrections or successful setup.

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

