# Implementation plan

Status: Approved for implementation on 2026-10-16; management and optional-image
scope amended by the project owner on the same date. Cards 02–03 remain in
development; Card 11 tracks the new management interface.

This plan implements the [confirmed requirements](discovery.md) and the
operating decisions approved in card 00.

## Deliverable

A Python/FastAPI LINE group bot, packaged with Docker, that manages each
group's restaurant list and selects lunch using a custom two-choice vote.
SQLite persists on Docker volumes. A restaurant requires only a name; an image
is optional. When supplied, retain its source HTTPS URL without downloading
image files. Management uses a rich menu and setup forms instead of chat Q&A.
Local development
uses `docker-compose.yml`; the server uses one standalone
`docker-compose-prod.yml`, without requiring a development override file.

## Confirmed behavior

| Situation | Expected behavior |
| --- | --- |
| Ordinary group conversation | Do not start a lunch selection. |
| Typed `@ginraidee-bot` before noon, two or more restaurants | Select two distinct restaurants with equal chances; show names, optional images, and voting buttons. |
| Typed `@ginraidee-bot`, one restaurant before noon | Announce that restaurant directly, explaining only one is available; no vote. |
| Typed `@ginraidee-bot` while a poll is open | Show the same choices and buttons; preserve votes and deadline. |
| Vote button | One vote per user per poll; another choice replaces it; repeated taps do not add votes. |
| Deadline | Close voting at 12:00 noon, Asia/Bangkok. |
| Tie or no votes | Select randomly between the poll's choices and explain the fallback. |
| Typed `@ginraidee-bot` at or after noon | Show today's result, or explain voting is closed if there is no result. |
| Typed `@ginraidee-bot manage` | Open the group's management menu and setup form; all group members may use it, without a sequence of chat questions. |
| Restaurant image input | Optional; allow a name-only entry. If supplied, accept and retain an HTTPS image URL and send that original URL to LINE. |
| Restaurant without an image | Show its name and available actions; omit the image component in catalogs, polls, and results. |
| Another group uses the bot | Keep catalogs, polls, votes, and management operations separate. |

Actual mention-list support, native LINE polls, a separate management service, direct
photo uploads, dish catalogs, AI-generated recommendations, and scheduled
creation of polls are outside the confirmed first-release scope.

## Approved operating decisions

Card 00 approved these decisions on 2026-10-16. They are implementation
requirements, not suggestions. The production hostname remains intentionally
deferred: it is not needed for local development and must be chosen before the
production release gate.

| ID | Area | Approved decision |
| --- | --- | --- |
| D1 | Edge cases and daily selection | Empty list: explain how to add restaurants. One final selection per group per Bangkok calendar day, including a single-restaurant result. Restaurants may appear again on later days. |
| D2 | Result delivery and restaurant changes | Announce results automatically at noon only for polls started by `@ginraidee-bot`. Keep poll choices as snapshots so edits/deletions do not change an existing vote. Closing a started poll is separate from creating a scheduled poll. |
| D3 | Management sessions | Isolate setup sessions by group and user; provide Cancel; expire after 10 minutes of inactivity; confirm deletions; reject blank names and duplicates after trimming/case normalization. Following the 2026-10-16 amendment, perform input through forms rather than chat prompts. First-release bot messages and setup UI are Thai. Keep message text centralized so a later language option does not alter domain rules. |
| D4 | Deployment and license | Each operator deploys independently with its own LINE credentials. Use the MIT License for the repository. The project owner chooses the public hostname and HTTPS termination approach before card 07 is accepted; this does not block local development. |
| D5 | People and models | The project owner is the CEO and owns final scope/release decisions and real LINE UAT. A separate Codex chat using `terra` with high reasoning performs the developer and tester roles. The current Codex chat is tech lead until handoff; each card records the actual execution environment. |
| D6 | Workflow and release gate | Use repository Markdown cards. One round is developer implementation/fix followed by tester verification. Maximum three rounds per card. After a failed third round, create a linked Bug and set the card Pending. Required acceptance failures hold dependent work and release unless the project owner explicitly accepts a reduced scope. |
| D7 | Data lifecycle | Store only necessary group/user identifiers and restaurant image URLs, never chat transcripts. Retain completed poll and delivery records for 90 days, then safely delete them. Backups preserve the SQLite database. Source image hosts control image-file retention. |
| D8 | Late, duplicate, and out-of-order webhooks | Verify signatures and persist a stable event identifier before effects. Duplicate identifiers produce no additional effects. Apply commands and votes by authoritative server processing time, not a client/event timestamp; at or after a poll deadline, reject writes even if the event was generated earlier. Existing poll/session version checks and database constraints govern otherwise out-of-order events. |
| D9 | Management and optional images, amended 2026-10-16 | `@ginraidee-bot manage` leads to menu/form setup; a native rich menu provides setup access in the Official Account's private chat. No chat Q&A for restaurant input. Name is required; image URL is optional and can be added, replaced, or removed. Existing catalog data and poll snapshots survive migration. Card 11 is required before production acceptance. |

## Management setup amendment (2026-10-16)

The project owner's request supersedes the original guided chat flow and
mandatory-image requirement. The owner selected a group menu card
opening a LINE in-app (LIFF) setup form, plus a private-chat rich menu opening
the same setup UI. Both entry points, menu/form behavior, and optional images
are confirmed.

- Use `@ginraidee-bot manage` and its existing aliases as management entry
  commands, separate from lunch selection. Show a group-scoped setup entry.
- Provide List, Add, Edit, and Delete in the setup UI. Add/Edit displays a
  required restaurant name and optional HTTPS image URL together, with Save
  and Cancel. Select entries visually instead of typing restaurant numbers;
  Delete requires an explicit confirmation action.
- Provide an explicit Remove image action when editing. Saving a name change
  preserves an existing image unless the user replaces or removes it. Blank
  image input on Add creates a name-only restaurant. Validate a supplied URL
  without downloading it; invalid input leaves the stored entry unchanged.
- Host the small setup UI and its API in the existing FastAPI deployment;
  no separate service is needed. Configure LIFF/LINE Login under the same
  provider as the Messaging API channel and verify identity on the server.
- Derive group context from signed group webhooks, not a browser-supplied group
  ID or LIFF chat context. Bind short-lived setup grants to the requesting
  group and verified user. Each member can obtain their own grant by invoking
  manage; copied links do not authorize another user. Private-menu access lists
  only that user's verified group contexts, with an explicit group selection
  and an instruction to run manage if none is available. Recheck current group
  membership for catalog access and writes; deny access if it cannot be verified.
- Keep the existing 10-minute inactivity limit, group ownership checks, stale
  edit/version protection, duplicate-name rules, and Thai copy. Form saves
  must be safe against double submission and must never start a lunch poll.
- Migrate image URLs to allow absence, preserving existing URLs. Poll snapshots
  preserve both an image URL and its absence. Do not create empty LINE image
  messages or require a placeholder image.

LINE describes native rich menus in the Official Account chat and notes they
are unavailable on desktop. Use a regular message/button entry in groups and
provide a setup link for desktop access. Native rich menus require their own
static menu artwork; optional restaurant photos are a separate requirement.
See the verified references below. Card 11 covers the interface and migration;
the previous Card 02–03 evidence describes the earlier chat implementation.

## Implementation architecture

Use a small single-server application rather than several independently
deployed application services.

```mermaid
flowchart LR
    Group[LINE group] --> LINE[LINE platform]
    LINE -->|Signed HTTPS webhooks| App[FastAPI bot]
    App -->|Replies and result push messages| LINE
    App --> DB[(SQLite on persistent volume)]
    Closing[Due-poll closure task] --> DB
    Closing --> App
```

- Keep webhook parsing/LINE transport separate from restaurant, poll, and vote
  behavior so tests can exercise the real rules without calling LINE.
- Verify the signature over the original request body before processing it.
  Dispatch the full command exactly so `@ginraidee-bot manage` is not mistaken
  for `@ginraidee-bot`. Route management to menu/form setup; ordinary chat
  messages must not be consumed as restaurant form input.
- Use SQLite transactions and constraints to enforce group ownership, one open
  poll, one vote per user/poll, and unique webhook processing. Do not rely only
  on process memory for these rules.
- Use one application worker and one active closer for the initial
  single-server deployment. Store due times in SQLite, scan for due polls, and
  recover them at startup. A process restart must not lose the schedule.
- Persist a poll's winner once. Persist outgoing result work with a stable
  delivery identity and bounded retries. Separate closing the vote from
  successfully sending a message; a LINE outage must not reopen voting or
  cause the winner to be re-randomized. Do not promise exactly-once delivery
  across the network; report unresolved delivery failures.
- Reject vote writes when authoritative server time is at or after the stored
  deadline, even if the closure task has not run. Store instants consistently
  and derive lunch dates/deadlines using Asia/Bangkok. Use an injectable clock
  for deadline tests. Apply the D8 server-time and idempotency rules to late,
  duplicate, and out-of-order webhooks.
- Use an OS-backed random generator for uniform sampling without replacement;
  do not weight restaurants. Deterministic fake randomness belongs only in
  tests.
- Allow absent image URLs; validate only supplied values as well-formed HTTPS
  URLs. The bot does not fetch source URLs
  or host image bytes; LINE retrieves the URL directly from its source host.
- Keep database writes short. Backups and restores preserve the SQLite database.

## Data model

| Record | Purpose and constraints |
| --- | --- |
| Group | LINE group identifier and relevant bot membership state. |
| Restaurant | Group owner, required display name, nullable HTTPS image URL, timestamps and row version. |
| Management session / setup grant | Verified group/user scope, form context, expiry, concurrency/version state; never trust a client-supplied group ID. |
| Poll | Group, lunch date, state, deadline, chosen result and reason; uniqueness according to D1. |
| Poll choice | Immutable restaurant name and optional-image snapshot tied to its poll. |
| Vote | Poll, voter identity, selected choice, update metadata; unique voter per poll. |
| Webhook receipt/work item | Unique event identity and durable processing state; transactionally coordinated with effects. |
| Outgoing result | Poll, delivery identity, state, attempt count, next retry and last error. |

Database uniqueness alone is not a processing strategy: if webhook work is
acknowledged before it is complete, persist work first and resume it after a
crash. Do not mark an event fully processed before its durable effects exist.

## Development phases and todo list

All task details and dependencies are in the [Kanban board](kanban.md).

| Phase | Cards | Expected demonstration / exit condition |
| --- | --- | --- |
| P0 — Review | 00 | Completed: operating decisions, responsibilities, and workflow approved. |
| P1 — Bot and catalog | 01–03, 11 | Start locally; process signed commands; manage group restaurants through menu/forms with optional HTTPS image URLs. |
| P2 — Selection and voting | 04–05 | Select eligible choices, handle one restaurant, reuse an open poll, cast and change votes safely. |
| P3 — Noon completion | 06 | Close at Bangkok noon, resolve normal/tie/no-vote outcomes, recover after restart, and deliver a stable result. |
| P4 — Deployment and qualification | 07–09 | Run the standalone production Compose setup, verify isolation/recovery, and give another operator complete setup documentation. |
| P5 — Manual acceptance | 10 | Tech lead and CEO review evidence and record manual UAT and release decisions. |

- [x] P0: Review card 00 and update this plan with accepted decisions.
- [ ] P1: Complete 01, 02, 03, and amendment Card 11 through developer/tester review.
- [ ] P2: Complete 04 and 05 through developer/tester review.
- [ ] P3: Complete 06, including restart and boundary-time tests.
- [ ] P4: Complete 07, 08, and 09; verify a clean operator setup.
- [ ] P5: Complete 10 with recorded manual results and defect disposition.

The phases describe delivery milestones, not separate teams. Work the first
card whose dependencies are Done. Card 01 is now the first Ready card. There
are no date or completion-time commitments yet.

## Validation and completion

Use pytest for meaningful rule/integration tests, signed webhook fixtures,
temporary SQLite databases, a controlled clock, and a fake LINE transport.
Use HTTPS URL fixtures and reserve real LINE group checks for manual UAT. Avoid
flaky statistical randomness tests:
verify sampling inputs, distinct choices, and fallback behavior deterministically.

Check concurrency, duplicate events, vote updates near noon, stale buttons,
isolation between two groups, name-only and mixed-image catalogs, image removal,
invalid/non-HTTPS supplied image URLs, setup identity/group authorization,
copied/expired setup links, restart during closure,
and failed outgoing delivery. Validate both Compose configurations and verify
data survives application container replacement. Do not use volume-deleting
commands during persistence acceptance checks.

Each card needs passing acceptance evidence, tester findings, tech-lead review,
and its required manual check. Phase P5 requires the [manual UAT checklist](uat.md)
and the [development workflow](development-workflow.md). No unchecked required
criterion may be silently marked Done.

## Verified platform references

- [LINE webhook handling](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
  documents signature checking and possible duplicate/out-of-order deliveries.
- [LINE sending messages](https://developers.line.biz/en/docs/messaging-api/sending-messages/)
  documents replies and group push messages. Noon announcements require push
  delivery rather than holding an old reply token; account quotas can affect it.
- [LINE image requirements](https://developers.line.biz/en/reference/messaging-api/#image-message)
  require HTTPS URLs when an image message is sent; name-only entries omit it.
- [LINE rich menus overview](https://developers.line.biz/en/docs/messaging-api/rich-menus-overview/)
  describes menu scope, static artwork, and desktop availability.
- [LIFF API reference](https://developers.line.biz/en/reference/liff/)
  documents LIFF context; do not assume it supplies an authoritative group ID.
- [LINE ID-token verification](https://developers.line.biz/en/docs/line-login/verify-id-token/)
  documents server-side identity verification for setup access.
- [Docker volumes](https://docs.docker.com/engine/storage/volumes/) describe
  persistent data outside a container's writable layer. A volume is not a backup.

Original references checked on 2026-10-15; management references checked on
2026-10-16. Runtime and dependency versions
will be pinned and verified when implementation starts.
