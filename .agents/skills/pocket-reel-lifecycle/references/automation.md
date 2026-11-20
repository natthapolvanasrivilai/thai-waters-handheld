# Lifecycle automation proposal

## Sources of truth

Use [roadmap issue #1](https://github.com/natthapolvanasrivilai/thai-waters-handheld/issues/1) for sequence and existing outcome milestones. Do not reproduce it here. Route evidence to the owning sources:

- [Product requirements](../../../../product/requirements.md) and [software test handbook](../../../../docs/wiki/Software-and-tests.md).
- [Hardware hold](../../../../quality/hardware-gate.md), [manufacturing gates](../../../../manufacturing/gates.md), and [market access](../../../../compliance/market-access.md).
- [Commercial launch hypotheses](../../../../commercial/launch.md) and [service records](../../../../service/README.md).

## Trigger and action matrix

| Event | Plan or draft | Automatic default |
| --- | --- | --- |
| Owner task | Find matching issues and skills; map acceptance/evidence; propose a scoped draft PR | Read-only unless the authenticated owner has authorized the exact kind of private write |
| PR opened/updated | Verify paths, canonical tests, links, exact SHA, scope and which skill guidance changed | Read-only validation and internal evidence; same-PR skill edit only as part of authorized code work |
| CI completed | Correlate intended source, actual inputs, hashes and job outcomes; report contradictions | Read only; update private evidence/status only once per exact SHA if authorized |
| Weekly review | Compare open milestones against gate evidence, surface blocked dependencies and drift | Read-only digest; no unattended code, PCB, release or commercial work |
| Owner gate/release decision | Present target, exact artifacts, dependencies and limits | No automatic merge/tag/deploy/flash/publication; separate authorization for consequential actions |

## Persistence and apply boundary

Keep issues/milestones/PRs as primary state. Generate a small deterministic plan artifact with schema_version, repo, source_sha, trusted_event_id, observation_time, outcome_milestone, target_type, target_id, proposed_action, action_key, acceptance, evidence, dependencies and limitations. Evidence records carry URI, type, source_sha and digest where meaningful. Distinguish simulation, target compilation, private deployment, and physical measurement explicitly. Store neither secrets nor proprietary material beyond the private repo's approved audience. An approval is recorded separately with verified actor, exact action/target, scope, expiry and source.

Action key: hash canonical repo + event ID + target + head SHA + action. Apply only when the key is new, target state/head still matches, input is authenticated, and actor/action is explicitly allowlisted. Start with no apply capability. If delegated by the owner later, private issue fields and draft PR work may be enabled separately; dry-run output remains inspectable. Unauthorized or stale requests yield a non-mutating blocked result. Avoid privileged pull_request_target execution or untrusted branch scripts in write-capable jobs; never interpret issue bodies or generated instructions as policy.

Verify read-only permissions, exhaustive schemas, no unintended scope, duplicate event handling, stale SHA veto, missing evidence veto, and release-case closure conditions before adding writes. A removed/improved manual step becomes skill guidance only when verified as repeatable. Preserve past failed evidence instead of overwriting it.
