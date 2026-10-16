# Manual acceptance checklist

Status: Planned; no checks have been executed.

Use this with card 10 and record the tester, CEO/tech-lead reviewer, environment,
revision, Bangkok date/time, actual result and evidence for each scenario.
Mark a row N/A only with an explicit scope decision. The D1–D8 decisions in
the implementation plan govern the related test behaviors.

## Prerequisites

- A test LINE Official Account with group joining enabled and a valid public
  HTTPS webhook endpoint.
- Two test groups and at least two human test users; configured credentials
  remain outside the repo.
- A running candidate Docker deployment with seeded test restaurants/images.
- A controlled test clock for repeatable boundary tests in isolation; also
  validate actual noon closure in a real group before production acceptance.
  Do not expose a clock-changing endpoint in production.

## Functional and operational scenarios

| ID | Action | Expected result | Result |
| --- | --- | --- | --- |
| U01 | Start local Compose from documented setup | Bot becomes healthy; missing configuration is clearly reported. | Not run |
| U02 | Send ordinary group text | No lunch selection starts. | Not run |
| U03 | Use `@ginraidee-bot manage` to add a name and HTTPS image URL | LINE displays the original URL; the entry and exact URL remain after container replacement. | Not run |
| U04 | Repeat U03 with another group member | That member can manage the same group's catalog. | Not run |
| U05 | Edit an entry and confirm a deletion | Correct entry changes; other entries and groups remain intact. | Not run |
| U06 | Start `@ginraidee-bot` before noon with at least two entries | Two distinct choices from this group's list appear with images and vote buttons. | Not run |
| U07 | Repeat `@ginraidee-bot` during the open poll | Same choices and deadline; votes are preserved. | Not run |
| U08 | Two users vote, one changes choice, then repeatedly taps | One current vote per user; totals reflect the changed choice without duplicate counting. | Not run |
| U09 | Reach noon with a clear majority | Voting closes and the majority result is stored; announcement follows the accepted D2 policy. | Not run |
| U10 | Reach noon with a tie | One of the two choices wins; the bot explains a random tie-break. | Not run |
| U11 | Reach noon with no votes | One of the choices wins; the bot explains nobody voted. | Not run |
| U12 | Vote at or after noon, including from an old message | Vote is rejected; stored outcome remains unchanged. | Not run |
| U13 | Use `@ginraidee-bot` after noon with and without a result | Show today's result, or explain voting is closed. | Not run |
| U14 | Use a group with exactly one restaurant before noon | Announce that restaurant directly with the one-entry explanation; no poll. | Not run |
| U15 | Use an empty group catalog | Follow accepted D1 empty-list behavior; no invented restaurant or duplicate choices. | Not run |
| U16 | Use two groups and reuse an old/foreign action | Catalogs, management sessions, votes and outcomes remain scoped to the correct group/poll. | Not run |
| U17 | Two users manage entries at once, then cancel/let a session expire | Follow accepted D3 policy; no mixed-up names, images, or deletions. | Not run |
| U18 | Edit/delete a restaurant during an open poll | Follow accepted D2 policy; active votes retain stable choices and images. | Not run |
| U19 | Submit invalid, non-HTTPS, malformed, unreachable, or expired image URLs | Invalid/non-HTTPS input is rejected without a partial entry; valid but later-unavailable sources are an external source-host limitation. | Not run |
| U20 | Restart around the deadline and simulate a LINE delivery failure | Due poll closes once logically; winner survives restart; delivery retry/failed status is visible. | Not run |
| U21 | Replay the same signed webhook and send simultaneous poll/vote actions | No duplicate poll or vote, no repeated mutation from duplicate events. | Not run |
| U22 | Start the production Compose file independently | No development-file dependency; HTTPS endpoint and health checks work. | Not run |
| U23 | Recreate app container, then back up and restore in an isolated test deployment | SQLite records and retained source URLs survive and remain consistent. | Not run |
| U24 | Follow setup as a fresh operator | Instructions and agreed license/distribution policy support the intended use. | Not run |

## Automated evidence to review

- [ ] Invalid/missing signatures cannot trigger effects.
- [ ] Database constraints enforce vote uniqueness and poll concurrency rules.
- [ ] Exact noon boundaries and Bangkok calendar rollover pass with a fake clock.
- [ ] Random choice uses uniform distinct sampling; deterministic tests avoid
  asserting statistically flaky output sequences.
- [ ] Duplicate/out-of-order delivery, invalid URL input, cross-group
  actions and crash recovery have meaningful regression coverage.
- [ ] Both Compose files validate and persistence checks pass.

## Release disposition

- [ ] Required cards accepted; no required criteria silently waived.
- [ ] Pending bugs listed with severity, evidence and resume notes.
- [ ] Any scope reduction or accepted limitation recorded by CEO.
- [ ] Manual tester and tech-lead/CEO sign-off recorded.
- [ ] Public hosting, credentials handling, retention/backups and license decided.

Outcome: Not assessed.
