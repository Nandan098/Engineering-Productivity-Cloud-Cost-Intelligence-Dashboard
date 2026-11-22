# Data model and table grain

## Logical relationship map

```text
                         teams
                       /   |   \\
                      /    |    \\
              engineers  sprints  capacity
                 |          |
                 |          |
              tasks <-------+
                 |
          assignee_id

teams -> deployments -> incidents (optional related_deployment_id)
teams -> cloud_costs
teams -> incidents
```

The production schema defines foreign keys from each fact table to `teams`, and from `tasks` to `sprints` and optional `engineers`. `incidents.related_deployment_id` is nullable.

## Table grain

| Table | Grain | Key |
|---|---|---|
| teams | One row per fictional engineering team | team_id |
| engineers | One row per fictional engineer | engineer_id |
| sprints | One row per team-specific sprint | sprint_id |
| tasks | One row per work item | task_id |
| deployments | One row per deployment event | deployment_id |
| cloud_costs | One row per team, service, environment and date | cost_id |
| capacity | One row per team and working day | date + team_id |
| incidents | One row per incident | incident_id |

## Important join cautions

- Join tasks to sprints using both `sprint_id` and `team_id` in analysis queries for defensive consistency.
- The `assignee_id` in tasks is nullable. An unassigned work item is not automatically a data error.
- `capacity` is already aggregated at team-day grain. Do not join it directly to task-level facts before summing, or hours will be duplicated.
- `cloud_costs` has multiple rows per team-day (service and environment split). Do not join it directly to tasks or deployment facts without pre-aggregating.
- The incident-to-deployment link should be used for investigation only, not as a causal label.
