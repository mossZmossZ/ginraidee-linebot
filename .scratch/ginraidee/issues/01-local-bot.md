# 01 — Run a local bot that safely receives group commands

**Phase:** P1
**Status:** In development
**Blocked by:** None — card 00 is complete.
**Owner:** Separate `terra`, high chat
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

Developer environment: current Codex workspace, Python 3.12.13 via `uv`.

Implemented the FastAPI webhook service, HMAC signature verification, exact
group-command dispatch, initial Thai replies, SQLite initialization and durable
webhook receipts. Added Docker/Compose configuration, private environment-file
handling, and local startup instructions.

Focused checks run:

- `uv run --group dev ruff check .` — passed.
- `uv run --group dev pytest` — 7 passed (one upstream Starlette deprecation
  warning).
- `LINE_CHANNEL_SECRET=compose-check-secret LINE_CHANNEL_ACCESS_TOKEN=compose-check-token docker compose config` — passed.
- Docker image build — not run: the local Docker daemon was unavailable
  (`~/.orbstack/run/docker.sock` did not exist).

Manual LINE check: not run; requires the CEO's credentials and a public HTTPS
tunnel.

| Round | Developer submission / checks | Tester result | Findings / next action |
| --- | --- | --- | --- |
| 1 | FastAPI/Docker foundation and focused checks recorded above | Not run | Await independent tester verification and local Docker smoke test once the daemon is running. |

Tech-lead review: Pending implementation review.
CEO/manual disposition: Not recorded.
Linked bugs / continuation: None recorded.

See the [workflow](../../../docs/development-workflow.md),
[implementation plan](../../../docs/implementation-plan.md), and
[board](../../../docs/kanban.md). Criteria depending on D1–D8 rules must follow
the decisions recorded in card 00.
