# Code Review Auto-Assignment

How GitHub auto-assignment is configured across ComplyTime teams
to distribute PR review workload fairly.

## Principles

- Auto-assignment is a **supporting tool** for fair workload distribution.
  It does not restrict who can review. Any maintainer or team member is
  free to review any PR at any time, regardless of whether the algorithm
  assigned them.
- The goal is to ensure no single person carries a disproportionate share
  of reviews while keeping the configuration simple to maintain.

## Algorithm Choice

GitHub offers two routing algorithms for auto-assignment: **Round Robin**
and **Load Balance**.

| Algorithm    | Selection criteria                        | Awareness of pending reviews |
|--------------|-------------------------------------------|------------------------------|
| Round Robin  | Least recent review request               | No                           |
| Load Balance | Total requests in a rolling 30-day window | Yes                          |

**Load Balance** is used for all teams because it accounts for each
member's outstanding review count, adapting to vacations, busy periods,
and varying review speeds. Round Robin only alternates by recency and does not account for
unfinished reviews, which can lead to uneven backlog accumulation.

For full details on algorithm behavior, see [References](#references).

## Current Configuration

Auto-assignment is enabled only on teams where it adds value. Teams
whose membership is fully covered by another auto-assigned team have
auto-assignment disabled to avoid redundant reviewer selection from
the same pool.

| Team                          | Auto-assignment | Algorithm    | Reviewers | Count existing requests | Notify         | Skipped members        |
|-------------------------------|-----------------|--------------|-----------|-------------------------|----------------|------------------------|
| `complytime-dev`              | Enabled         | Load Balance | 2         | Yes                     | --             | *(onboarding members)* |
| `complytime-approvers`        | Enabled         | Load Balance | 2         | Yes                     | --             | --                     |
| `ampel-provider-approvers`    | Disabled        | --           | --        | --                      | Requested only | --                     |
| `openscap-provider-approvers` | Disabled        | --           | --        | --                      | Requested only | --                     |
| `opa-provider-approvers`      | Disabled        | --           | --        | --                      | Requested only | --                     |

**Count existing requests** must be enabled on all auto-assigned teams.
Without it, a member who belongs to multiple requested teams can consume
a reviewer slot in each team independently, reducing the number of
distinct reviewers on a PR.

**Only notify requested team members** must be enabled on provider
teams (shown as "Requested only" above). Without auto-assignment,
CODEOWNERS requests trigger a team-level review request that notifies
all team members by default. Enabling this setting limits notifications
to members who are already individually requested (e.g., those assigned
by `complytime-dev` auto-assignment), preventing duplicate notifications
to the rest of the team.

## Why Provider Teams Don't Use Auto-Assignment

The three provider teams (`ampel-provider-approvers`,
`openscap-provider-approvers`, `opa-provider-approvers`) exist for
organizational identity and repository permissions, but their
auto-assignment is disabled because:

1. **Full membership overlap**: Every technical maintainer in the
   provider teams is also a member of `complytime-dev`.
2. **CODEOWNERS coverage**: All CODEOWNERS files include
   `complytime-dev`, so its auto-assignment already selects reviewers
   for provider paths.
3. **CODEOWNERS satisfaction**: Since any reviewer assigned by
   `complytime-dev` is also a member of the provider teams, their
   review satisfies the CODEOWNERS branch protection requirement for
   both teams simultaneously.
4. **No redundant slots**: Enabling auto-assignment on provider teams
   would draw from the same pool a second (or third) time, wasting
   reviewer slots without adding distinct reviewers.

Since auto-assignment is disabled on these teams, "Only notify
requested team members" must also be enabled to prevent all team
members from being notified on every CODEOWNERS-triggered request.
With this setting, only members already individually assigned (via
`complytime-dev` auto-assignment) receive notifications from the
provider team request.

If provider teams diverge in membership in the future (specialized
reviewers per provider), re-enabling auto-assignment on those teams
should be reassessed.

## CODEOWNERS Interaction

Branch protection rules require CODEOWNERS review. When a team listed
in CODEOWNERS has auto-assignment enabled:

1. GitHub requests the team as a reviewer.
2. Auto-assignment replaces the team with individual members.
3. However, branch protection prevents the team request from being
   removed until a team member approves.
4. Once an assigned individual (who is a member of the team) approves,
   the team request is satisfied and removed.

In practice, the PR shows both the team and the assigned individuals
until the review is completed.

## Onboarding New Members

When a new member joins a team with auto-assignment enabled:

1. **Add them to the skip list**: In the team's code review settings,
   add the member to "Never assign certain team members." This prevents
   the algorithm from overloading them with reviews before they are
   familiar with the codebase.
2. **Voluntary reviews still count**: While on the skip list, the
   member can still review any PR they feel comfortable with. Their
   approval satisfies CODEOWNERS branch protection as long as they are
   a member of the owning team.
3. **Remove from skip list when ready**: Once the member is ramped up,
   remove them from the skip list. Load Balance will gradually include
   them in assignments based on their review history.

## Reassessment Checklist

Revisit this configuration when:

- A new member is added to or removed from a team -- check
  [`peribolos.yaml`](https://github.com/complytime/.github/blob/main/peribolos.yaml)
  for membership overlap and overload risk.
- Provider teams diverge in membership from `complytime-dev` -- consider
  re-enabling auto-assignment on those teams.
- A new team with overlapping members is created -- evaluate whether
  auto-assignment is needed or redundant.
- The effective reviewer pool for any team drops below 4 -- the
  algorithm has limited room to distribute, increasing per-person load.
- Review workload feels uneven despite Load Balance -- verify that
  "Count existing requests" is enabled and check for members in many
  teams.

## References

- [Managing code review settings for your team](https://docs.github.com/en/organizations/organizing-members-into-teams/managing-code-review-settings-for-your-team) -- GitHub documentation covering auto-assignment configuration, routing algorithms, and team notification settings.
