# Field-level data dictionary

## teams.csv
- team_id: Team key.
- team_name/domain: Fictional team and engineering domain.
- headcount: Deliberately unequal team size.
- monthly_cloud_budget_inr: Illustrative monthly budget, not actual spend.

## engineers.csv
- engineer_id: Synthetic engineer key; no real employee identities.
- team_id: Foreign key to teams.
- role/career_level/experience_years: Synthetic role attributes.
- employment_type/standard_weekly_hours: Contract type and standard weekly hours.

## sprints.csv
- sprint_id: Team-specific sprint key.
- team_id: Foreign key to teams.
- sprint_number: 1–13 for each team.
- start_date/end_date: Two-week sprint dates.
- planned_capacity_hours: Sum of team-day available hours during the sprint.

## tasks.csv
- task_id: Unique work-item key.
- team_id/sprint_id/assignee_id: Team, sprint and optional engineer foreign keys.
- task_type/priority/status: Work classification, priority and workflow status.
- story_points: Fibonacci-like sizing; zero denotes unpointed support work.
- is_committed: Whether the task was in the original sprint commitment.
- created_at/started_at/completed_at/last_updated_at: Synthetic timestamps.
- blocked_days/cycle_time_days: Blocked-duration proxy and active elapsed cycle time for completed tasks.

## deployments.csv
- deployment_id: Unique deployment key.
- team_id/engineer_id/service_name: Owner and service.
- environment: Production, Staging or Development.
- deployed_at/status/duration_minutes: Time, result and duration.
- rollback_flag/commit_count/is_emergency: Deployment attributes.

## cloud_costs.csv
- cost_id: Unique cost line key.
- date/team_id/service_name/environment: Daily ledger grain.
- cost_inr: Simulated actual cost in INR.
- budget_inr: Illustrative daily budget allocation.
- currency: INR.

## capacity.csv
- date/team_id: One row per team per working day.
- active_headcount: Team members active after simulated leave.
- available_hours/logged_hours: Available capacity and recorded work.
- delivery_hours/support_hours/incident_hours/meeting_and_admin_hours: Work mix components.
- overtime_hours: Logged hours exceeding available hours.

## incidents.csv
- incident_id: Unique incident key.
- team_id/service_name: Owning team and affected service.
- started_at/resolved_at/status: Incident lifecycle; unresolved records have blank resolved_at.
- severity/category: Priority and classification.
- affected_users_estimate/customer_impact_minutes: Synthetic impact estimates.
- related_deployment_id: Optional recent deployment association, not proof of causation.
- suspected_change_related: Simulated triage hypothesis, not a verified root cause.
