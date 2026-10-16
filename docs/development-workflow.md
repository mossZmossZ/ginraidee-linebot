# Development workflow

Status: Approved in card 00 on 2026-10-16. Card 01 is complete by project-owner
confirmation; Card 02 is in development.

## Roles

| Role | Model / effort requested | Responsibility |
| --- | --- | --- |
| Project owner (CEO) | Human | Set direction, resolve material product decisions, perform real LINE UAT, review manual evidence and accept delivery. |
| Tech lead | Current Codex chat | Own plan, phases, cards, expected functionality, dependencies, code review and reports until handoff. |
| Developer | Separate `terra`, high chat | Implement one card, run focused checks, fix verified defects and record evidence. |
| Tester | Separate `terra`, high chat | Verify acceptance criteria, test failures/boundaries, and report reproducible findings. |

The project owner performs real LINE testing. Record actual commands,
revisions, checks, and execution environment in each card. Planning approval
does not itself claim that application work has started.

## Per-card execution

1. CEO and tech lead agree on the reviewed plan and material decisions.
2. Tech lead checks the selected card's dependencies, todo list, acceptance
   criteria and expected behavior; then marks it Ready.
3. Developer implements the card and records the changes plus focused checks.
4. Tester verifies against the criteria, rather than accepting the developer's
   report alone, and records Pass/Fail plus reproducible defects.
5. If it passes, tech lead reviews it and reports the result to CEO. Perform the
   applicable manual LINE check and record who ran it, when, and what happened.
6. If it fails, developer and tester may repeat within the three-round maximum.
7. If the third round fails, stop that loop. Mark the card Pending, create a Bug,
   and preserve a concrete continuation note. Report it to tech lead and CEO.

Definition: one round is one developer implementation/fix submission
followed by tester verification. The first submission is round 1; at most two
further fix-and-verification submissions remain. Failed verification is not an
excuse to create a new parent card and reset the count.

Dependency/release rule: a Pending card does not unblock dependents.
Independent cards may proceed; failed required criteria hold release unless the
CEO explicitly accepts and documents a reduced scope. Resuming a held fix needs
a recorded decision and bounded follow-up work; do not continue automatically
beyond the agreed cap.

## Evidence and round log

Every card includes a todo list, acceptance criteria, dependency list, round log,
manual check and handoff section. Add evidence as work happens.

| Round | Developer changes / checks | Tester result / evidence | Defects / next action |
| --- | --- | --- | --- |
| 1 | Not started | Not run | — |
| 2 | Not started | Not run | — |
| 3 | Not started | Not run | — |

Record commands and results, environment, revision or relevant diff, and useful
test output. Do not put LINE tokens, secrets, user chat transcripts, or public
group identifiers in cards or screenshots. Report a failed/unrun check plainly.

## Bug card template

```markdown
# BUG-NNN — Short description

Status: Open / Pending / In development / In testing / Review / Done
Parent card:
Severity and affected behavior:
Rounds already used:
Environment and revision:

## Reproduce
1. Prerequisite
2. Action

Expected:
Actual:
Evidence:

## Continuation
What was tried:
Current hypothesis:
Next concrete step:
Dependencies and required decisions:
Resume decision / remaining allowed rounds:

## Verification
- [ ] Regression scenario passes.
- [ ] Parent acceptance criteria rechecked.
- [ ] Tech lead / CEO disposition recorded.
```

## Phase report

At each milestone, tech lead reports:

- Delivered behavior and completed cards.
- Automated checks and manual evidence, including what was not run.
- Open/Pending bugs, rounds used, and affected dependencies.
- Scope deviations and decisions needed.
- Recommendation to accept the milestone, revise scope, or hold it.

Use the [Kanban board](kanban.md) as the status index. Update the card and board
together; the report must not claim implementation or UAT that has not happened.
