# 01 — Run a local bot that safely receives group commands

**Phase:** P1
**Status:** Done
**Blocked by:** None — card 00 is complete.
**Owner:** Separate `terra`, high chat
**Developer/tester rounds used:** 1 / 3

## What to build

An operator starts the Dockerized bot locally, and a signed LINE group command reaches the bot and receives an initial setup response.

## Todo

- [x] Add the Python/FastAPI application, pinned dependencies and local Compose setup.
- [x] Add configuration, health checking and SQLite initialization on persistent storage.
- [x] Validate the raw-body webhook signature and route exact group commands.
- [x] Add focused signed-webhook and container startup checks.

## Acceptance criteria

- [x] Documented local startup reaches a healthy bot with persistent SQLite storage.
- [x] A valid signed group @ginrai command reaches the command handler and, for an empty catalog, follows the accepted D1 setup behavior.
- [x] @ginrai-manage reaches its own management entry point rather than starting a poll.
- [x] Ordinary messages, unsupported chat sources and invalid signatures create no lunch-selection effects.
- [x] Secrets are supplied through environment/configuration and are absent from committed files and logs.
- [x] Restarting the app preserves initialized persistent state.

## Verification

Signed/invalid webhook fixtures, exact-command dispatch, temporary SQLite initialization and local Compose smoke check.

Manual check: Operator starts the local container and sends an initial command in a test LINE group through a configured HTTPS tunnel/endpoint.

## Evidence and handoff

Developer environment: current Codex workspace, Python 3.12.13 via `uv`.
Relevant diff: `b80a063c1321c17d7c20b64f315c42fac592e227...HEAD` on
`codex/card-01-local-bot`.

Implemented the FastAPI webhook service, HMAC signature verification, exact
group-command dispatch, initial Thai replies, SQLite initialization and durable
webhook receipts. Added Docker/Compose configuration, private environment-file
handling, and local startup instructions.

Focused checks run:

- `uv run --group dev ruff check .` — passed.
- `uv run --group dev pytest` — 8 passed (one upstream Starlette deprecation
  warning).
- `LINE_CHANNEL_SECRET=compose-check-secret LINE_CHANNEL_ACCESS_TOKEN=compose-check-token docker compose config` — passed.
- Docker 29.4.0 smoke check with placeholder credentials — image build passed;
  `docker compose up -d` reached a healthy `/healthz` response; SQLite was
  present in `/data`; after `docker compose restart bot`, `/healthz` remained
  healthy and the database file remained present. The test container was then
  stopped with `docker compose down` without deleting the named volume.

Manual LINE check: project owner confirmed Card 01 complete on 2026-10-16.
The external UAT details were not supplied to this workspace.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| 1 | FastAPI/Docker foundation, durable webhook-work recovery, and focused checks recorded above | Project owner confirmed completion | Card closed by owner confirmation. |

Tech-lead review: Two-axis review found durable webhook recovery incomplete;
the work item is now stored atomically with its group effect and resumes after
a failed delivery/restart.
CEO/manual disposition: Project owner confirmed completion on 2026-10-16.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules must follow
the decisions recorded in card 00.
