# Power BI model and dashboard guide

## 1. Import

Use **Get data → Text/CSV** and import the eight files from `data/raw/`. Keep the names as shown below. Convert the date fields to Date or Date/Time types as indicated. Disable automatic date/time if you prefer to use the explicit date table below.

- `teams` (dimension)
- `engineers` (dimension)
- `sprints` (dimension)
- `tasks` (fact)
- `deployments` (fact)
- `cloud_costs` (fact)
- `capacity` (fact)
- `incidents` (fact)

## 2. Relationships

Create one-to-many, single-direction relationships from dimensions to facts:

| One side | Many side | Active? |
|---|---|---|
| `teams[team_id]` | `engineers[team_id]` | Yes |
| `teams[team_id]` | `sprints[team_id]` | Yes |
| `teams[team_id]` | `tasks[team_id]` | Yes |
| `teams[team_id]` | `deployments[team_id]` | Yes |
| `teams[team_id]` | `cloud_costs[team_id]` | Yes |
| `teams[team_id]` | `capacity[team_id]` | Yes |
| `teams[team_id]` | `incidents[team_id]` | Yes |
| `sprints[sprint_id]` | `tasks[sprint_id]` | Yes |
| `engineers[engineer_id]` | `tasks[assignee_id]` | Yes |
| `engineers[engineer_id]` | `deployments[engineer_id]` | Yes |

Avoid bi-directional relationships unless you have a specific, tested reason. For date reporting, add a calendar dimension and a date-only column for timestamp facts. Use inactive relationships for alternate task dates (created/completed) if you need both analyses.

## 3. Add date columns

In Power Query, add these date-only columns (or use calculated columns):

- `deployments[deployment_date]` from `deployed_at`
- `incidents[incident_date]` from `started_at`
- `tasks[created_date]` from `created_at`
- `tasks[completed_date]` from `completed_at`

Use `cloud_costs[date]` and `capacity[date]` directly. Create a calendar table with DAX below and relate it to one date field per fact as required. If you activate multiple date relationships from one calendar to one fact, keep only one active at a time.

## 4. Suggested report pages

1. **Engineering Overview:** committed-point completion, production deployment failure rate, cloud spend vs budget, weighted utilization, resolved incident MTTR.
2. **Sprint Productivity:** committed vs completed points by sprint, task status mix, cycle time by task type, backlog ageing.
3. **Deployment Performance:** production deployments by month, successful/failed count, failure and rollback rates, team breakdown.
4. **Cloud Cost Intelligence:** monthly actual vs budget, service/environment spend, variance %, daily outlier table.
5. **Capacity & Reliability:** logged vs available hours, work-hour mix, utilization trend, incident count and MTTR by severity.

## 5. Important interpretation notes

- Story points are team-relative. Use sprint completion trends within a team; avoid ranking teams by raw velocity as though story points were standardized.
- Production deployment frequency should be scoped to `environment = Production`. Show event volume alongside failure rate so low-volume rates are not over-interpreted.
- Utilization is a weighted ratio: `SUM(logged_hours) / SUM(available_hours)`. High utilization is not automatically positive and can indicate little capacity buffer.
- MTTR uses resolved incidents only; leave open incidents out of the average.
- Cloud budget is an illustrative daily allocation. It is not a vendor invoice or actual contract value.
- Incident-to-deployment links are synthetic triage metadata, not evidence that the deployment caused the incident.
- This is fictional synthetic data, not Zepto or any company's internal data.
