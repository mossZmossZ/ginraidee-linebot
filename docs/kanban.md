# Development Kanban

Status: Card 01 is in development. No application card has passed independent
testing or manual acceptance yet.

The board and [individual cards](../.scratch/ginraidee/issues/) form the local
planning tracker. Cards are not published to GitHub or another external tracker.
Dependencies and review gates must be satisfied before moving a card to Ready.

## Board

| Backlog / Todo | Ready | In development | In testing | Tech lead / CEO review | Pending / Bug | Done |
| --- | --- | --- | --- | --- | --- | --- |
| 02–10: see card list below | — | 01: Local bot | — | — | — | 00: Plan and operating decisions |

The planning bundle alone does not mark an application card Done. Card 00 was
accepted on 2026-10-16; card 01 has an implementation submission but remains
subject to independent testing, review, and the required manual LINE check.

## Cards and dependencies

| Card | Phase | Deliverable | Blocked by | Status | Role on start |
| --- | --- | --- | --- | --- | --- |
| [00](../.scratch/ginraidee/issues/00-review-plan.md) | P0 | Confirm scope, defaults, people/models, workflow | None | Done | Project owner + current Codex chat |
| [01](../.scratch/ginraidee/issues/01-local-bot.md) | P1 | Local bot receives signed commands | 00 | In development | Current Codex workspace |
| [02](../.scratch/ginraidee/issues/02-add-restaurants.md) | P1 | Add/view restaurants and host persistent images | 01 | Todo | Developer |
| [03](../.scratch/ginraidee/issues/03-edit-delete.md) | P1 | Edit/delete restaurants through group management | 02 | Todo | Developer |
| [04](../.scratch/ginraidee/issues/04-start-selection.md) | P2 | Start or reuse a lunch selection | 02 | Todo | Developer |
| [05](../.scratch/ginraidee/issues/05-vote.md) | P2 | Cast/change one vote per person | 04 | Todo | Developer |
| [06](../.scratch/ginraidee/issues/06-close-polls.md) | P3 | Close at noon and deliver/recover results | 05 | Todo | Developer |
| [07](../.scratch/ginraidee/issues/07-production.md) | P4 | Standalone production Compose and recovery | 03, 06 | Todo | Developer |
| [08](../.scratch/ginraidee/issues/08-qualification.md) | P4 | Qualify isolation, failures, and concurrency | 07 | Todo | Developer + tester |
| [09](../.scratch/ginraidee/issues/09-operator-docs.md) | P4 | Fresh-operator setup and contribution docs | 07 | Todo | Developer |
| [10](../.scratch/ginraidee/issues/10-manual-acceptance.md) | P5 | Manual acceptance and final report | 08, 09 | Todo | Tester + tech lead + CEO |

This is a dependency graph, not an instruction to use parallel agents. Card 04
does not depend on restaurant editing because addition is enough to exercise
selection; integration with edits/deletions is verified before production.

## Card movement

1. Tech lead moves a reviewed, dependency-free Todo card to Ready.
2. Developer takes one Ready card and marks it In development.
3. Tester verifies its acceptance criteria and marks it In testing.
4. A failure returns to development while fewer than three rounds have run.
5. Passing evidence goes to Tech lead / CEO review and its manual check.
6. Only accepted work becomes Done. A failed third round becomes Pending,
   with a linked Bug, reproduction, and continuation notes.

Round counting and release gates are approved in the workflow. See
[development-workflow.md](development-workflow.md) for the full rule.

## Defect register

No defects have been observed: code has not been written or tested.

| Bug | Affected card | Severity | Rounds used | Reproduction / evidence | Next action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — | — |

When a defect is found, add a dedicated Bug card using the template in the
workflow. Preserve a Pending parent and its dependency links; do not silently
reset the round counter or imply that unverified work passed.
