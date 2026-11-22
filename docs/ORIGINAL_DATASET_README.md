# Engineering Productivity & Cloud Cost Intelligence Dataset

## Important notice
This is a **synthetic dataset for a fictional quick-commerce / technology organization**. It is **not Zepto data** and contains no actual company, employee, infrastructure or financial records. It is suitable for portfolio practice only.

## Coverage and size
- Date range: 2026-05-04 to 2026-11-01 (13 two-week sprint cycles)
- Teams: 7 with deliberately different headcounts and operating profiles
- Engineers: 50
- Tasks: 939
- Deployments: 684
- Daily cloud cost lines: 19110
- Team-day capacity records: 910
- Incidents: 148
- Random seed: 20261122

The data is intentionally **non-uniform**: teams differ in size, ticket volume, sprint outcomes, deployment cadence, cloud budgets, utilization and incident volume. There is natural random variation at task, day and event level. No team has identical metrics or equal allocation. These patterns are illustrative assumptions—not measured industry benchmarks or claims about real organizations.

## Files
All tables are CSV files in `datasets/`: `teams`, `engineers`, `sprints`, `tasks`, `deployments`, `cloud_costs`, `capacity`, `incidents`.
- `docs/data_dictionary.csv`: table grain and purpose
- `docs/field_level_data_dictionary.md`: column definitions
- `sql/schema_postgresql.sql`: starter relational schema

## Relationships
- `teams.team_id` -> `engineers.team_id`, `sprints.team_id`, `tasks.team_id`, `deployments.team_id`, `cloud_costs.team_id`, `capacity.team_id`, `incidents.team_id`
- `sprints.sprint_id` -> `tasks.sprint_id`
- `engineers.engineer_id` -> `tasks.assignee_id` (nullable) and `deployments.engineer_id`
- `deployments.deployment_id` -> `incidents.related_deployment_id` (nullable)

## Suggested KPI definitions
- Sprint commitment completion % = completed story points for committed tasks / committed story points * 100.
- Sprint velocity = completed story points; specify whether uncommitted work is included.
- Production deployment frequency = successful Production deployments per team/week or month.
- Production deployment failure rate = failed Production deployments / all Production deployments * 100.
- Rollback rate = Production deployments with rollback_flag=true / all Production deployments * 100.
- MTTR = mean resolved_at minus started_at for resolved incidents, converted to hours.
- Cloud cost variance % = (actual cost - allocated budget) / allocated budget * 100.
- Resource utilization % = logged_hours / available_hours * 100. Sustained high utilization can indicate overload, not necessarily better performance.
- Task cycle time = average `cycle_time_days` for completed tasks. Compare similar task types and sizes.

## Analytical cautions
1. Do not infer causation from temporal association between a deployment and an incident. `related_deployment_id` is a simulated triage association only.
2. Story points are team-relative; avoid treating raw velocity as directly comparable across teams.
3. Some Support tasks have zero story points; exclude or report them separately for velocity.
4. Compare teams with their size, task mix, service criticality and support load in mind.
5. Unresolved incidents have blank `resolved_at`; exclude these from MTTR.
6. `budget_inr` is an illustrative daily allocation derived from a fictional monthly budget—not an invoice or vendor quote.
7. Synthetic variation is useful for practicing analysis but is not evidence about any real company.

## Suggested analysis questions
- Which teams have the largest gap between committed and completed points?
- How do completion and cycle time vary by work type, priority and sprint?
- Which teams deploy most frequently to Production, and how do failure/rollback rates compare?
- Which services/environments consume the most cloud spend?
- Which service-day costs exceed their allocated daily budget?
- Is high utilization associated with older tasks or more incident work?
- How does MTTR vary by severity and team?
