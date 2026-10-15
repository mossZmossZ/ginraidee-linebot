# LINE application discovery

Status: Core requirements captured; implementation planning bundle drafted for review
Started: 2026-10-15

Next documents: [implementation plan and phases](implementation-plan.md),
[Kanban board and cards](kanban.md), [development workflow](development-workflow.md),
and [manual UAT](uat.md). Planning is written; application implementation and
agent execution have not started.

## Confirmed scope

- Create a LINE application in this repository.
- Work through requirements in an interactive interview.
- Save the resulting requirements and decisions as repository documentation.

## Repository baseline at the start of discovery

The repository currently contains only a README naming the project
`ginraidee-linebot`. No application code or technology stack is present.

## Interview approach

The initial interview used one question at a time. After 21 question prompts
(including one repeated question), the user raised the interview length.
Consolidate remaining decisions for review instead of continuing granular
follow-ups. Keep recommendations separate from confirmed requirements. Begin
implementation after the user confirms the shared understanding and scope.

## Confirmed product requirements

- Build a LINE bot that randomly suggests restaurants for lunch.
- Publish the project as open source so other people can obtain and use it.
- Clarify unclear design decisions with the user before implementation.

### Group lunch selection and voting

- Invite the bot into a LINE group.
- Invoke `@ginrai` to randomly select two restaurant choices and create a vote
  in the group.
- A lunch poll starts only when a user invokes `@ginrai`; it must not start
  automatically on a schedule or in response to ordinary group conversation.
  Use the literal typed command `@ginrai` to start a poll and the literal typed
  command `@ginrai-manage` for management. The user's "yes" was interpreted as
  acceptance of this recommendation; actual LINE mention support is not part
  of the confirmed scope.
- Confirmed: use a custom bot voting message with two restaurant buttons.
  The bot records votes and rejects voting after the agreed deadline.
- Random selection gives every restaurant in the group's catalog an equal
  chance and selects two distinct restaurants when at least two are available,
  without weighting or preferences. With only one saved restaurant, use that
  restaurant rather than requiring members to add another. The user rejected
  a minimum-two-restaurants restriction. The user originally described this
  as "true random"; the randomness implementation and repeats across days
  remain undecided. With one restaurant, announce it directly without a poll
  and explain that only one restaurant is available, as confirmed by the user.
  Behavior with an empty catalog still needs clarification.
- Voting closes at 12:00 noon in Asia/Bangkok (Thailand time), as confirmed
  by the user. This replaces the earlier wording "before 12:00".
- Each LINE user has one vote per poll and may change their choice before
  the deadline. Choosing the other restaurant replaces the previous vote;
  repeated taps on the same choice do not add votes.
- Each group may have only one open poll. Repeating `@ginrai` while it is open
  shows the existing choices and voting buttons without changing the choices,
  resetting votes, or changing the closing deadline.
- At or after 12:00 noon in Asia/Bangkok, `@ginrai` does not open a new poll.
  It shows today's result if a poll was held; otherwise it explains that voting
  is closed and asks the user to start a poll before noon the next day.
- If both restaurants receive an equal, nonzero number of votes, the bot
  randomly selects the winner and announces that a random tie-break was used.
- If nobody votes by the deadline, the bot randomly chooses one of the two
  restaurants and announces that nobody voted.
- Invoke `@ginrai-manage` to add, edit, and delete restaurant entries.
- Each entry represents a restaurant (a place to eat), with a restaurant name
  and an image source. The earlier phrase `menu name` means the restaurant's
  name; a separate dish catalog is not required.
- Restaurant images are provided as pasted HTTPS image URLs in the first
  release. Uploading photos in LINE is outside the confirmed first-release scope.
- Each LINE group has its own separate catalog. `@ginrai-manage` changes only
  that group's entries, and `@ginrai` selects only from that group's catalog.
- Every member of a group may use `@ginrai-manage` to add, edit, or delete that
  group's entries. Designated manager restrictions are not required.
- `@ginrai-manage` opens a guided flow inside the LINE group chat, with Add,
  Edit, and Delete buttons and prompts for restaurant names and image URLs.
  No separate management website is required for the first release. Replies
  to management prompts belong to that flow and do not start lunch polls.

### Confirmed backend image storage

The user accepted backend-hosted copies of restaurant images:

1. A group member provides the restaurant's HTTPS image URL.
2. The backend downloads and validates the image.
3. The image is stored on a persistent Docker volume so replacing or restarting
   the application container does not discard it.
4. The backend serves the stored image at a publicly accessible HTTPS URL for
   LINE to display. The source URL can be retained as metadata.

The [LINE image message requirements](https://developers.line.biz/en/reference/messaging-api/#image-message)
specify HTTPS image URLs. The backend therefore needs a publicly reachable
HTTPS image endpoint; a private filesystem path alone is insufficient.
Image validation, download limits, protection against fetching private network
addresses, and image cleanup/retention will need to be defined before implementation.
This design preserves URL input; direct photo uploads remain outside the
confirmed first-release scope.

### Reference and platform findings (2026-10-15)

- User-provided inspiration: [LINE food random / Cloudflare Workers article](https://medium.com/linedevth/line-food-random-x-cloudflare-workers-edb12972616d).
  The article could not be retrieved during discovery. Its contents have not
  been verified; the functional requirements above come from the user.
  This reference does not change the approved Python/FastAPI/Docker stack.
- The [LINE Messaging API reference](https://developers.line.biz/en/reference/messaging-api/)
  lists no native group-poll creation or closing endpoint. Based on that public
  API surface, automatic creation and closure of LINE's built-in group polls
  should not be assumed supported.
- [LINE postback actions](https://developers.line.biz/en/docs/messaging-api/actions/#postback-action)
  send button interactions to the bot server. The user accepted a custom voting
  message with two choices and server-managed votes instead of a native LINE
  group poll.

Whether other people deploy their own bots or use a shared hosted bot remains
unresolved. An open-source license has not yet been chosen.

## Confirmed technology and deployment requirements

- Application language: Python, with Python script files.
- Web framework: FastAPI.
- Package and run the application with Docker.
- Use SQLite for restaurant records, polls, and votes, within the user's
  authorization to use SQLite for persistence. Store the database file on a
  persistent Docker volume. Store downloaded images as files on persistent
  Docker storage, with their references in SQLite.
- Local development configuration: `docker-compose.yml`.
- Server configuration: a single `docker-compose-prod.yml`.

Python version, dependencies, server environment, and public webhook
connectivity have not yet been decided.

## Requested development roles

| Role | Requested model | Reasoning effort | Responsibility |
| --- | --- | --- | --- |
| Development CEO | Not specified | Not specified | Oversight and final manual review with the tech lead |
| Tech lead | `sol` | High | Create cards or phases, a todo list, and expected functionality; review reports |
| Developer | `terra` | High | Implement the work and fix reported defects |
| Tester | `terra` | High | Test the application and report defects |

Model names above preserve the user's wording. Exact model identifiers and
availability must be resolved before configuring or starting agents. No model
substitution is approved. Whether the CEO is the user or an agent, and who
performs manual tests, still needs clarification.

## Confirmed development workflow

1. CEO provides direction to the tech lead.
2. Tech lead creates cards or phases with todo items and expected functionality.
3. Developer writes code; tester tests it and returns defects for fixes.
4. Repeat the developer/tester loop at most three times.
5. Report the outcome to the tech lead and CEO for manual testing again.
6. If the issue cannot be fixed within the limit, record it as Pending and Bug,
   hold the fix, and preserve it for later continuation.

The exact meaning of one loop, where cards are stored, the reporting format,
and whether unresolved defects block a phase or release are still undecided.
This records the requested process; implementation and agent execution have
not started.

## Consolidated remaining decisions

The main product behavior is captured above. The following proposals are not
confirmed requirements and do not authorize implementation or agent execution.
There is no active one-at-a-time interview question.

| Area | Proposed default or unresolved decision |
| --- | --- |
| Empty catalog and daily selection | Propose an add-restaurants prompt for an empty catalog, one final selection per group per day (including a sole restaurant), and allowing restaurants to repeat on later days. |
| Poll completion and catalog changes | Propose an automatic result message at noon for a previously started poll; retain the original restaurant names and images for that poll when the catalog changes. |
| Management flow | Propose a separate session per group member, cancellation and expiry, and confirmation before deletion. |
| Distribution and hosting | Independent deployment with each operator's own LINE credentials was recommended but remains unanswered. Server domain, HTTPS setup, and open-source license remain undecided. |
| Development roles | CEO identity, manual testing ownership, and exact `sol`/`terra` model identifiers need confirmation before agents run. |
| Cards and defect loop | Propose Markdown cards in the repo, with acceptance criteria; one loop means implementation/fix followed by tester verification, at most three rounds per card. Remaining defects become Pending/Bug. Release-blocking rules remain undecided. |

The implementation plan now proposes image download validation/limits,
retention handling, minimal user identifiers, backups, restart recovery, webhook
verification/duplicate handling, and acceptance checks together. Material product
choices are collected in its D1–D7 review table and card 00. Writing that plan
does not turn the proposals into accepted requirements or authorize agent
execution. Repository-local draft cards fulfill the requested planning work;
retaining that tracker for development remains part of the consolidated review.
