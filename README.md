# ginraidee-linebot

A planned open-source LINE group bot for choosing where to eat lunch.
Members manage their group's restaurants with `@ginraidee-bot manage` and
start selection with `@ginraidee-bot`. The legacy `@ginrai` commands and the
hyphenated `@ginraidee-bot-manage` spelling remain supported for compatibility.
Voting closes at 12:00 noon, Thailand time.

Planned stack: Python, FastAPI, SQLite, and Docker with persistent database
storage. Restaurant images are optional HTTPS source URLs. Local and server
deployments will use `docker-compose.yml` and `docker-compose-prod.yml`
respectively.

## Project status

Card 01 (the local bot foundation) is complete by project-owner confirmation.
Card 02 (group restaurant catalogs and image URLs) is awaiting tester and
manual LINE verification. Card 03 (restaurant editing and deletion) is in
development under project-owner direction while Card 02 verification remains
pending.

The 2026-10-16 plan amendment adds menu/form setup and optional restaurant
images in [Card 11](.scratch/ginraidee/issues/11-management-setup.md). This
interface is planned; the current implementation still uses chat prompts and
requires an image URL.

## Planning documents

- [Confirmed requirements and decision history](docs/discovery.md)
- [Implementation plan, development phases, and todo list](docs/implementation-plan.md)
- [Kanban board and task-card index](docs/kanban.md)
- [Individual task cards](.scratch/ginraidee/issues/)
- [Roles, review workflow, and three-round defect limit](docs/development-workflow.md)
- [Manual acceptance checklist](docs/uat.md)

Start with the implementation plan and board. The public production hostname
and HTTPS termination approach are intentionally deferred until the production
deployment card; they do not block local development.

## Local development (Card 01)

Prerequisites: Docker Desktop and credentials from a LINE Messaging API channel.

1. Copy `.env.example` to `.env` and set `LINE_CHANNEL_SECRET` and
   `LINE_CHANNEL_ACCESS_TOKEN`. Keep `.env` private; it is ignored by Git.
2. Start the bot with `docker compose up --build`.
3. Confirm `http://localhost:8000/healthz` returns `{"status":"ok"}`.
4. Configure a public HTTPS tunnel to `http://localhost:8000/callback` in the
   LINE Developers Console, then add the bot to a test group and send
   `@ginraidee-bot`. An empty group receives the Thai prompt to use
   `@ginraidee-bot manage`.

The `ginraidee_data` named volume holds the SQLite database. `docker compose
down` keeps it; do not use `docker compose down --volumes` when checking
persistence. Stop the local bot with `docker compose down`.

## Planned restaurant management

Send `@ginraidee-bot manage` in a group to open a menu card and its setup form.
The bot's private-chat rich menu opens the same form. Add, view, edit, and delete
restaurants using the form, without chat Q&A. Only the restaurant name is
required; an HTTPS image URL is optional and can be added, replaced, or removed.
Name-only restaurants remain eligible for selection and voting. Setup is scoped
to the verified member and group, with Cancel, deletion confirmation, and
10-minute inactivity expiry. See the [amended plan](docs/implementation-plan.md).

## Current restaurant management (before Card 11)

In a group, send `@ginraidee-bot manage` and choose `เพิ่ม` to add a restaurant,
`รายการ` to view the catalog, `แก้ไข` to update a restaurant, or `ลบ` to delete
one. Edit and delete list restaurant numbers; send the displayed number to
select the entry. Edits require a new name and HTTPS image URL. Deletion takes
effect only after `ยืนยัน`; send `ยกเลิก` at any step to leave the restaurant
unchanged. Management sessions are scoped to the group and member and expire
after 10 minutes of inactivity.
