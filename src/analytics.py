"""Reusable analytics functions for the Engineering Productivity project."""
from __future__ import annotations

from pathlib import Path
from typing import Dict
import pandas as pd
import numpy as np

TABLES = [
    "teams", "engineers", "sprints", "tasks", "deployments",
    "cloud_costs", "capacity", "incidents"
]


def load_data(data_dir: str | Path) -> Dict[str, pd.DataFrame]:
    """Load all project CSVs and apply consistent date parsing."""
    data_dir = Path(data_dir)
    missing = [name for name in TABLES if not (data_dir / f"{name}.csv").exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required CSV files in {data_dir}: {', '.join(missing)}"
        )

    data = {name: pd.read_csv(data_dir / f"{name}.csv") for name in TABLES}
    date_cols = {
        "sprints": ["start_date", "end_date"],
        "tasks": ["created_at", "started_at", "completed_at", "last_updated_at"],
        "deployments": ["deployed_at"],
        "cloud_costs": ["date"],
        "capacity": ["date"],
        "incidents": ["started_at", "resolved_at"],
    }
    for table, columns in date_cols.items():
        for col in columns:
            data[table][col] = pd.to_datetime(data[table][col], errors="coerce")

    # Normalize boolean columns without assuming the CSV parser's dtype inference.
    for table, columns in {
        "tasks": ["is_committed"],
        "deployments": ["rollback_flag", "is_emergency"],
        "incidents": ["suspected_change_related"],
    }.items():
        for col in columns:
            if data[table][col].dtype != bool:
                data[table][col] = (
                    data[table][col].astype(str).str.strip().str.lower()
                    .map({"true": True, "false": False, "1": True, "0": False})
                )

    return data


def data_as_of_date(data: Dict[str, pd.DataFrame]) -> pd.Timestamp:
    """Return the final sprint end date used for reproducible backlog ageing."""
    return pd.to_datetime(data["sprints"]["end_date"]).max().normalize()


def build_sprint_kpis(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    tasks = data["tasks"].copy()
    sprints = data["sprints"][
        ["sprint_id", "team_id", "sprint_number", "start_date", "end_date", "sprint_goal"]
    ].copy()
    tasks["story_points"] = pd.to_numeric(tasks["story_points"], errors="coerce").fillna(0)
    tasks["is_done"] = tasks["status"].eq("Done")
    tasks["committed_points"] = np.where(tasks["is_committed"], tasks["story_points"], 0)
    tasks["completed_committed_points"] = np.where(
        tasks["is_committed"] & tasks["is_done"], tasks["story_points"], 0
    )
    tasks["completed_points_all"] = np.where(tasks["is_done"], tasks["story_points"], 0)
    out = tasks.groupby(["team_id", "sprint_id"], as_index=False).agg(
        task_count=("task_id", "count"),
        committed_task_count=("is_committed", "sum"),
        completed_task_count=("is_done", "sum"),
        committed_points=("committed_points", "sum"),
        completed_committed_points=("completed_committed_points", "sum"),
        completed_points_all=("completed_points_all", "sum"),
    )
    out["commit_completion_pct"] = np.where(
        out["committed_points"] > 0,
        100 * out["completed_committed_points"] / out["committed_points"], np.nan
    )
    out = out.merge(sprints, on=["team_id", "sprint_id"], how="left")
    team_names = data["teams"][["team_id", "team_name"]]
    return out.merge(team_names, on="team_id", how="left").sort_values(["team_name", "sprint_number"])


def build_team_task_summary(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    tasks = data["tasks"].copy()
    tasks["story_points"] = pd.to_numeric(tasks["story_points"], errors="coerce").fillna(0)
    tasks["committed_points"] = np.where(tasks["is_committed"], tasks["story_points"], 0)
    tasks["completed_committed_points"] = np.where(
        tasks["is_committed"] & tasks["status"].eq("Done"), tasks["story_points"], 0
    )
    tasks["cycle_time_days"] = pd.to_numeric(tasks["cycle_time_days"], errors="coerce")
    tasks["blocked_days"] = pd.to_numeric(tasks["blocked_days"], errors="coerce").fillna(0)
    summary = tasks.groupby("team_id", as_index=False).agg(
        task_count=("task_id", "count"),
        done_tasks=("status", lambda s: s.eq("Done").sum()),
        blocked_tasks=("status", lambda s: s.eq("Blocked").sum()),
        open_tasks=("status", lambda s: s.ne("Done").sum()),
        committed_points=("committed_points", "sum"),
        completed_committed_points=("completed_committed_points", "sum"),
        mean_cycle_time_days=("cycle_time_days", "mean"),
        median_cycle_time_days=("cycle_time_days", "median"),
        mean_blocked_days=("blocked_days", "mean"),
    )
    summary["task_completion_pct"] = 100 * summary["done_tasks"] / summary["task_count"]
    summary["commit_completion_pct"] = np.where(
        summary["committed_points"] > 0,
        100 * summary["completed_committed_points"] / summary["committed_points"], np.nan
    )
    return summary.merge(data["teams"][["team_id", "team_name", "headcount"]], on="team_id", how="left")


def build_backlog(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    tasks = data["tasks"].copy()
    cutoff = data_as_of_date(data)
    tasks["created_at"] = pd.to_datetime(tasks["created_at"])
    tasks["age_days_as_of_dataset_end"] = (
        cutoff - tasks["created_at"].dt.normalize()
    ).dt.days.clip(lower=0)
    backlog = tasks.loc[tasks["status"].ne("Done")].copy()
    backlog["cycle_time_days"] = pd.to_numeric(backlog["cycle_time_days"], errors="coerce")
    backlog = backlog.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")
    return backlog.sort_values("age_days_as_of_dataset_end", ascending=False)


def build_deployment_kpis(data: Dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    deployments = data["deployments"].copy()
    deployments["deployed_at"] = pd.to_datetime(deployments["deployed_at"])
    prod = deployments.loc[deployments["environment"].eq("Production")].copy()
    prod["month"] = prod["deployed_at"].dt.to_period("M").astype(str)
    monthly = prod.groupby(["team_id", "month"], as_index=False).agg(
        production_deployments=("deployment_id", "count"),
        successful_deployments=("status", lambda s: s.eq("Success").sum()),
        failed_deployments=("status", lambda s: s.eq("Failed").sum()),
        rollbacks=("rollback_flag", "sum"),
        median_duration_minutes=("duration_minutes", "median"),
    )
    monthly["failure_rate_pct"] = 100 * monthly["failed_deployments"] / monthly["production_deployments"]
    monthly["rollback_rate_pct"] = 100 * monthly["rollbacks"] / monthly["production_deployments"]
    monthly = monthly.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")

    summary = prod.groupby("team_id", as_index=False).agg(
        production_deployments=("deployment_id", "count"),
        successful_deployments=("status", lambda s: s.eq("Success").sum()),
        failed_deployments=("status", lambda s: s.eq("Failed").sum()),
        rollbacks=("rollback_flag", "sum"),
        emergency_deployments=("is_emergency", "sum"),
    )
    summary["failure_rate_pct"] = 100 * summary["failed_deployments"] / summary["production_deployments"]
    summary["rollback_rate_pct"] = 100 * summary["rollbacks"] / summary["production_deployments"]
    weeks = max((prod["deployed_at"].max() - prod["deployed_at"].min()).days / 7, 1)
    summary["successful_production_deployments_per_week"] = summary["successful_deployments"] / weeks
    summary = summary.merge(data["teams"][["team_id", "team_name", "headcount"]], on="team_id", how="left")
    return monthly, summary


def build_cloud_kpis(data: Dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cloud = data["cloud_costs"].copy()
    cloud["date"] = pd.to_datetime(cloud["date"])
    cloud["month"] = cloud["date"].dt.to_period("M").astype(str)
    cloud["variance_inr"] = cloud["cost_inr"] - cloud["budget_inr"]
    cloud["variance_pct"] = np.where(
        cloud["budget_inr"] > 0, 100 * cloud["variance_inr"] / cloud["budget_inr"], np.nan
    )
    monthly = cloud.groupby(["team_id", "month"], as_index=False).agg(
        actual_cost_inr=("cost_inr", "sum"),
        budget_inr=("budget_inr", "sum"),
        cost_records=("cost_id", "count"),
    )
    monthly["variance_inr"] = monthly["actual_cost_inr"] - monthly["budget_inr"]
    monthly["variance_pct"] = 100 * monthly["variance_inr"] / monthly["budget_inr"]
    monthly = monthly.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")

    by_service = cloud.groupby(["team_id", "service_name", "environment"], as_index=False).agg(
        actual_cost_inr=("cost_inr", "sum"), budget_inr=("budget_inr", "sum")
    )
    by_service["variance_inr"] = by_service["actual_cost_inr"] - by_service["budget_inr"]
    by_service["variance_pct"] = 100 * by_service["variance_inr"] / by_service["budget_inr"]
    by_service = by_service.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")

    detail = cloud.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")
    detail["over_budget_25_pct"] = detail["cost_inr"] > 1.25 * detail["budget_inr"]
    return monthly, by_service, detail


def build_capacity_kpis(data: Dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    capacity = data["capacity"].copy()
    capacity["date"] = pd.to_datetime(capacity["date"])
    capacity["month"] = capacity["date"].dt.to_period("M").astype(str)
    monthly = capacity.groupby(["team_id", "month"], as_index=False).agg(
        available_hours=("available_hours", "sum"),
        logged_hours=("logged_hours", "sum"),
        delivery_hours=("delivery_hours", "sum"),
        support_hours=("support_hours", "sum"),
        incident_hours=("incident_hours", "sum"),
        meeting_and_admin_hours=("meeting_and_admin_hours", "sum"),
        overtime_hours=("overtime_hours", "sum"),
        team_days=("date", "nunique"),
    )
    monthly["utilization_pct"] = np.where(
        monthly["available_hours"] > 0,
        100 * monthly["logged_hours"] / monthly["available_hours"], np.nan
    )
    monthly = monthly.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")

    overall = capacity.groupby("team_id", as_index=False).agg(
        available_hours=("available_hours", "sum"),
        logged_hours=("logged_hours", "sum"),
        delivery_hours=("delivery_hours", "sum"),
        support_hours=("support_hours", "sum"),
        incident_hours=("incident_hours", "sum"),
        meeting_and_admin_hours=("meeting_and_admin_hours", "sum"),
        overtime_hours=("overtime_hours", "sum"),
    )
    overall["utilization_pct"] = 100 * overall["logged_hours"] / overall["available_hours"]
    overall = overall.merge(data["teams"][["team_id", "team_name", "headcount"]], on="team_id", how="left")
    return monthly, overall


def build_incident_kpis(data: Dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    inc = data["incidents"].copy()
    inc["started_at"] = pd.to_datetime(inc["started_at"])
    inc["resolved_at"] = pd.to_datetime(inc["resolved_at"])
    inc["mttr_hours"] = (inc["resolved_at"] - inc["started_at"]).dt.total_seconds() / 3600
    by_team_severity = inc.groupby(["team_id", "severity"], as_index=False).agg(
        incident_count=("incident_id", "count"),
        open_incidents=("status", lambda s: s.eq("Open").sum()),
        resolved_incidents=("status", lambda s: s.eq("Resolved").sum()),
        mean_mttr_hours=("mttr_hours", "mean"),
        median_mttr_hours=("mttr_hours", "median"),
        affected_users_estimate=("affected_users_estimate", "sum"),
        customer_impact_minutes=("customer_impact_minutes", "sum"),
    )
    by_team_severity = by_team_severity.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")

    team_summary = inc.groupby("team_id", as_index=False).agg(
        incident_count=("incident_id", "count"),
        open_incidents=("status", lambda s: s.eq("Open").sum()),
        resolved_incidents=("status", lambda s: s.eq("Resolved").sum()),
        mean_mttr_hours=("mttr_hours", "mean"),
        p1_incidents=("severity", lambda s: s.eq("P1").sum()),
    )
    team_summary = team_summary.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")
    return by_team_severity, team_summary


def build_task_type_kpis(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    tasks = data["tasks"].copy()
    tasks["cycle_time_days"] = pd.to_numeric(tasks["cycle_time_days"], errors="coerce")
    out = tasks.groupby(["team_id", "task_type"], as_index=False).agg(
        tasks=("task_id", "count"),
        done_tasks=("status", lambda s: s.eq("Done").sum()),
        mean_cycle_time_days=("cycle_time_days", "mean"),
        median_cycle_time_days=("cycle_time_days", "median"),
        mean_story_points=("story_points", "mean"),
    )
    out["done_pct"] = 100 * out["done_tasks"] / out["tasks"]
    return out.merge(data["teams"][["team_id", "team_name"]], on="team_id", how="left")


def run_all_analyses(data: Dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Return all analysis tables used by the app and written to outputs."""
    deploy_monthly, deploy_team = build_deployment_kpis(data)
    cloud_monthly, cloud_service, cloud_detail = build_cloud_kpis(data)
    capacity_monthly, capacity_team = build_capacity_kpis(data)
    incident_severity, incident_team = build_incident_kpis(data)
    return {
        "sprint_kpis_by_team_sprint": build_sprint_kpis(data),
        "team_task_summary": build_team_task_summary(data),
        "backlog_as_of_dataset_end": build_backlog(data),
        "production_deployments_by_team_month": deploy_monthly,
        "production_deployment_team_summary": deploy_team,
        "cloud_cost_by_team_month": cloud_monthly,
        "cloud_cost_by_service_environment": cloud_service,
        "cloud_cost_detail": cloud_detail,
        "capacity_by_team_month": capacity_monthly,
        "capacity_team_summary": capacity_team,
        "incidents_by_team_severity": incident_severity,
        "incident_team_summary": incident_team,
        "task_type_summary": build_task_type_kpis(data),
    }
