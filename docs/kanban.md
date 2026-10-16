# Development Kanban

Status: Card 02 is in development, awaiting tester verification and its
required manual LINE check. Card 03 implementation is in development under
project-owner direction before Card 02's verification is complete. Card 01 is
complete by project-owner confirmation.

The board and [individual cards](../.scratch/ginraidee/issues/) form the local
planning tracker. Cards are not published to GitHub or another external tracker.
Dependencies and review gates must be satisfied before moving a card to Ready.

## Board

| Backlog / Todo | Ready | In development | In testing | Tech lead / CEO review | Pending / Bug | Done |
| --- | --- | --- | --- | --- | --- | --- |
| 04–10: see card list below | — | 02: Restaurant catalog; 03: Edit/delete restaurants (owner-authorized early start) | — | — | — | 00: Plan and operating decisions; 01: Local bot |

The planning bundle alone does not mark an application card Done. Card 00 was
accepted on 2026-10-16 and Card 01 was subsequently confirmed complete by the
project owner. Card 02 has not passed its verification and manual gates. On
2026-10-16, the project owner authorized Card 03 implementation to begin while
Card 02 verification remains pending; this does not mark Card 02 Done or waive
Card 03's review and manual acceptance gates.

## Cards and dependencies

| Card | Phase | Deliverable | Blocked by | Status | Role on start |
| --- | --- | --- | --- | --- | --- |
| [00](../.scratch/ginraidee/issues/00-review-plan.md) | P0 | Confirm scope, defaults, people/models, workflow | None | Done | Project owner + current Codex chat |
| [01](../.scratch/ginraidee/issues/01-local-bot.md) | P1 | Local bot receives signed commands | 00 | Done | Current Codex workspace |
| [02](../.scratch/ginraidee/issues/02-add-restaurants.md) | P1 | Add/view restaurants and retain image URLs | 01 | In development | Current Codex workspace |
| [03](../.scratch/ginraidee/issues/03-edit-delete.md) | P1 | Edit/delete restaurants through group management | 02 (owner-authorized implementation start before verification) | In development | Current Codex workspace by owner direction |
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

No open defects are recorded. Card 01's initial review found incomplete durable
webhook recovery; it was corrected and covered by a regression test.

| Bug | Affected card | Severity | Rounds used | Reproduction / evidence | Next action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — | — |

When a defect is found, add a dedicated Bug card using the template in the
workflow. Preserve a Pending parent and its dependency links; do not silently
reset the round counter or imply that unverified work passed.
