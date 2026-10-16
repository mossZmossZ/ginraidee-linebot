# LINE application discovery

Status: Requirements and operating decisions approved; implementation is in progress
Started: 2026-10-15

Next documents: [implementation plan and phases](implementation-plan.md),
[Kanban board and cards](kanban.md), [development workflow](development-workflow.md),
and [manual UAT](uat.md). Card 00 approved the plan on 2026-10-16; Card 01 is
complete by project-owner confirmation and Card 02 is in development.

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
- Invoke `@ginraidee-bot` to randomly select two restaurant choices and create a vote
  in the group.
- A lunch poll starts only when a user invokes `@ginraidee-bot`; it must not start
  automatically on a schedule or in response to ordinary group conversation.
  Use the literal typed command `@ginraidee-bot` to start a poll and
  `@ginraidee-bot manage` for management. The legacy `@ginrai` and
  `@ginrai-manage` commands, plus the hyphenated `@ginraidee-bot-manage`
  spelling, remain supported for compatibility. Actual LINE mention support
  is not part of the confirmed scope.
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
- Each group may have only one open poll. Repeating `@ginraidee-bot` while it is open
  shows the existing choices and voting buttons without changing the choices,
  resetting votes, or changing the closing deadline.
- At or after 12:00 noon in Asia/Bangkok, `@ginraidee-bot` does not open a new poll.
  It shows today's result if a poll was held; otherwise it explains that voting
  is closed and asks the user to start a poll before noon the next day.
- If both restaurants receive an equal, nonzero number of votes, the bot
  randomly selects the winner and announces that a random tie-break was used.
- If nobody votes by the deadline, the bot randomly chooses one of the two
  restaurants and announces that nobody voted.
- Invoke `@ginraidee-bot manage` to add, edit, and delete restaurant entries.
- Each entry represents a restaurant (a place to eat), with a restaurant name
  and an image source. The earlier phrase `menu name` means the restaurant's
  name; a separate dish catalog is not required.
- Restaurant images are provided as pasted HTTPS image URLs in the first
  release. Uploading photos in LINE is outside the confirmed first-release scope.
- Each LINE group has its own separate catalog. `@ginraidee-bot manage` changes
  only that group's entries, and `@ginraidee-bot` selects only from that group's catalog.
- Every member of a group may use `@ginraidee-bot manage` to add, edit, or delete that
  group's entries. Designated manager restrictions are not required.
- `@ginraidee-bot manage` opens a guided flow inside the LINE group chat, with Add,
  Edit, and Delete buttons and prompts for restaurant names and image URLs.
  No separate management website is required for the first release. Replies
  to management prompts belong to that flow and do not start lunch polls.

### Confirmed restaurant image URL behavior

The project owner changed the image decision on 2026-10-16: restaurant records
retain only the HTTPS image URL supplied by a group member. The bot sends that
same URL to LINE; it does not download, validate image bytes, or store a copy
on a Docker volume. Direct photo uploads remain outside the first-release scope.

The [LINE image message requirements](https://developers.line.biz/en/reference/messaging-api/#image-message)
still require HTTPS image URLs. Source hosts remain responsible for availability
and may change, expire, or block an image after it is saved.

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

Each operator deploys their own bot using their own LINE credentials. The
repository uses the MIT License. The project owner will choose the public
hostname and HTTPS termination approach before production deployment.

## Confirmed technology and deployment requirements

- Application language: Python, with Python script files.
- Web framework: FastAPI.
- Package and run the application with Docker.
- Use SQLite for restaurant records, polls, and votes, within the user's
  authorization to use SQLite for persistence. Store the database file on a
  persistent Docker volume; restaurant records retain their original HTTPS
  image URLs, not image files.
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

The project owner is the CEO and performs real LINE manual acceptance testing.
The current Codex chat is tech lead until handoff. A separate `terra`, high
reasoning chat performs developer and tester work; each card records its actual
execution environment.

## Confirmed development workflow

1. CEO provides direction to the tech lead.
2. Tech lead creates cards or phases with todo items and expected functionality.
3. Developer writes code; tester tests it and returns defects for fixes.
4. Repeat the developer/tester loop at most three times.
5. Report the outcome to the tech lead and CEO for manual testing again.
6. If the issue cannot be fixed within the limit, record it as Pending and Bug,
   hold the fix, and preserve it for later continuation.

One loop is a developer implementation/fix submission followed by tester
verification; it is recorded in repository-local Markdown cards. A maximum of
three rounds applies to each card. A failed third round creates a linked Bug
and keeps the parent Pending; Pending required work blocks dependents and
release unless the project owner explicitly accepts a reduced scope.

## Approved operating decisions

Card 00 approved the following rules on 2026-10-16. The public production
hostname remains deferred to card 07 and does not block local development.

| Area | Approved decision |
| --- | --- |
| Empty catalog and daily selection | Show an add-restaurants prompt for an empty catalog; create one final selection per group per Bangkok day (including a sole restaurant); allow restaurants to repeat on later days. |
| Poll completion and catalog changes | Automatically announce the result at noon for an `@ginraidee-bot` poll; retain original restaurant names and images in poll snapshots after catalog edits/deletions. |
| Management flow | Use separate sessions per group member, Cancel, 10-minute inactivity expiry, deletion confirmation, and Thai first-release message text. |
| Distribution and hosting | Operators deploy independently with their own credentials; the repository is MIT licensed. The project owner chooses the server domain and HTTPS setup before production deployment. |
| Development roles | The project owner is CEO and manual LINE-UAT owner. The current Codex chat is tech lead until handoff; a separate `terra`, high chat performs development and testing. |
| Cards and defect loop | Use repository Markdown cards with acceptance criteria; one loop is implementation/fix plus verification; maximum three rounds; remaining defects become linked Pending/Bug work and hold dependencies/releases unless the project owner approves reduced scope. |
| Late, duplicate, and out-of-order webhooks | Persist a verified stable event identifier before effects; duplicates are idempotent. Use authoritative server processing time for command/vote deadlines, rejecting post-deadline writes regardless of event timestamp. |

The implementation plan defines HTTPS URL validation, 90-day operational-record
retention, minimal user identifiers, backups, restart
recovery, webhook verification/duplicate handling, and acceptance checks.
Card 00 authorizes the first implementation card; the tracker remains
repository-local for development.
