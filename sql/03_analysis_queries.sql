-- Query 1: Sprint commitment completion by team and sprint.
-- Story points are team-relative; compare trends within a team, not as a standardized league table.
SELECT
    t.team_name,
    s.sprint_number,
    s.sprint_id,
    SUM(CASE WHEN k.is_committed THEN k.story_points ELSE 0 END) AS committed_points,
    SUM(CASE WHEN k.is_committed AND k.status = 'Done' THEN k.story_points ELSE 0 END) AS completed_committed_points,
    ROUND(
        100.0 * SUM(CASE WHEN k.is_committed AND k.status = 'Done' THEN k.story_points ELSE 0 END)
        / NULLIF(SUM(CASE WHEN k.is_committed THEN k.story_points ELSE 0 END), 0), 2
    ) AS commit_completion_pct
FROM tasks k
JOIN teams t USING (team_id)
JOIN sprints s USING (sprint_id, team_id)
GROUP BY t.team_name, s.sprint_number, s.sprint_id
ORDER BY t.team_name, s.sprint_number;

-- Query 2: Work-in-progress and task-cycle profile by team.
SELECT
    t.team_name,
    COUNT(*) AS total_tasks,
    COUNT(*) FILTER (WHERE k.status = 'Done') AS done_tasks,
    COUNT(*) FILTER (WHERE k.status = 'Blocked') AS blocked_tasks,
    COUNT(*) FILTER (WHERE k.status <> 'Done') AS open_tasks,
    ROUND(AVG(k.cycle_time_days) FILTER (WHERE k.status = 'Done'), 2) AS avg_completed_cycle_days,
    ROUND(AVG(k.blocked_days), 2) AS avg_blocked_days
FROM tasks k
JOIN teams t USING (team_id)
GROUP BY t.team_name
ORDER BY total_tasks DESC;

-- Query 3: Production deployment reliability by team and month.
SELECT
    t.team_name,
    DATE_TRUNC('month', d.deployed_at)::date AS deployment_month,
    COUNT(*) AS production_deployments,
    COUNT(*) FILTER (WHERE d.status = 'Success') AS successful_deployments,
    COUNT(*) FILTER (WHERE d.status = 'Failed') AS failed_deployments,
    ROUND(100.0 * COUNT(*) FILTER (WHERE d.status = 'Failed') / NULLIF(COUNT(*), 0), 2) AS failure_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE d.rollback_flag) / NULLIF(COUNT(*), 0), 2) AS rollback_rate_pct
FROM deployments d
JOIN teams t USING (team_id)
WHERE d.environment = 'Production'
GROUP BY t.team_name, DATE_TRUNC('month', d.deployed_at)::date
ORDER BY deployment_month, t.team_name;

-- Query 4: Cloud spend versus allocated budget by team and month.
SELECT
    t.team_name,
    DATE_TRUNC('month', c.date)::date AS cost_month,
    ROUND(SUM(c.cost_inr), 2) AS actual_cost_inr,
    ROUND(SUM(c.budget_inr), 2) AS allocated_budget_inr,
    ROUND(SUM(c.cost_inr) - SUM(c.budget_inr), 2) AS variance_inr,
    ROUND(100.0 * (SUM(c.cost_inr) - SUM(c.budget_inr)) / NULLIF(SUM(c.budget_inr), 0), 2) AS variance_pct
FROM cloud_costs c
JOIN teams t USING (team_id)
GROUP BY t.team_name, DATE_TRUNC('month', c.date)::date
ORDER BY cost_month, t.team_name;

-- Query 5: Cloud spend by service and environment.
SELECT
    t.team_name,
    c.service_name,
    c.environment,
    ROUND(SUM(c.cost_inr), 2) AS actual_cost_inr,
    ROUND(SUM(c.budget_inr), 2) AS allocated_budget_inr,
    ROUND(100.0 * (SUM(c.cost_inr) - SUM(c.budget_inr)) / NULLIF(SUM(c.budget_inr), 0), 2) AS variance_pct
FROM cloud_costs c
JOIN teams t USING (team_id)
GROUP BY t.team_name, c.service_name, c.environment
ORDER BY actual_cost_inr DESC;

-- Query 6: Weighted resource utilization and work mix by team/month.
-- Weighted utilization = total logged hours / total available hours.
SELECT
    t.team_name,
    DATE_TRUNC('month', c.date)::date AS capacity_month,
    ROUND(SUM(c.available_hours), 2) AS available_hours,
    ROUND(SUM(c.logged_hours), 2) AS logged_hours,
    ROUND(100.0 * SUM(c.logged_hours) / NULLIF(SUM(c.available_hours), 0), 2) AS utilization_pct,
    ROUND(SUM(c.delivery_hours), 2) AS delivery_hours,
    ROUND(SUM(c.support_hours), 2) AS support_hours,
    ROUND(SUM(c.incident_hours), 2) AS incident_hours,
    ROUND(SUM(c.overtime_hours), 2) AS overtime_hours
FROM capacity c
JOIN teams t USING (team_id)
GROUP BY t.team_name, DATE_TRUNC('month', c.date)::date
ORDER BY capacity_month, t.team_name;

-- Query 7: MTTR by team and severity. Open incidents have no resolved_at and are excluded.
SELECT
    t.team_name,
    i.severity,
    COUNT(*) AS incident_count,
    COUNT(*) FILTER (WHERE i.status = 'Open') AS open_incidents,
    ROUND(AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.started_at)) / 3600)
        FILTER (WHERE i.resolved_at IS NOT NULL), 2) AS mean_mttr_hours
FROM incidents i
JOIN teams t USING (team_id)
GROUP BY t.team_name, i.severity
ORDER BY t.team_name, i.severity;

-- Query 8: Open backlog ageing at the synthetic dataset cut-off date (2026-11-01).
-- This is a reproducible historical snapshot, not the current age of backlog today.
WITH dataset_cutoff AS (
    SELECT MAX(end_date) AS as_of_date FROM sprints
)
SELECT
    t.team_name,
    k.task_id,
    k.task_type,
    k.priority,
    k.status,
    k.created_at::date AS created_date,
    (dc.as_of_date - k.created_at::date) AS age_days_as_of_dataset_end,
    k.blocked_days
FROM tasks k
JOIN teams t USING (team_id)
CROSS JOIN dataset_cutoff dc
WHERE k.status <> 'Done'
ORDER BY age_days_as_of_dataset_end DESC;

-- Query 9: High cloud-cost records (>25% above the allocated daily budget).
SELECT
    t.team_name, c.date, c.service_name, c.environment,
    c.cost_inr, c.budget_inr,
    ROUND(100.0 * (c.cost_inr - c.budget_inr) / NULLIF(c.budget_inr, 0), 2) AS variance_pct
FROM cloud_costs c
JOIN teams t USING (team_id)
WHERE c.cost_inr > 1.25 * c.budget_inr
ORDER BY variance_pct DESC;

-- Query 10: Incident-to-deployment triage links.
-- This is an association for investigation only; it does not establish causation.
SELECT
    t.team_name,
    i.incident_id,
    i.started_at,
    i.severity,
    i.category,
    i.related_deployment_id,
    d.deployed_at,
    d.status AS deployment_status,
    i.suspected_change_related
FROM incidents i
JOIN teams t USING (team_id)
LEFT JOIN deployments d ON d.deployment_id = i.related_deployment_id
WHERE i.related_deployment_id IS NOT NULL
ORDER BY i.started_at;
