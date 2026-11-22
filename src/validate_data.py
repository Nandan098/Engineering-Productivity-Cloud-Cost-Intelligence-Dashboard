"""Run structural, referential and basic business-rule checks on the CSV data."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from analytics import load_data


def validate(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    checks: list[dict] = []

    def add(name: str, passed: bool, detail: str, severity: str = "ERROR") -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "severity": severity, "detail": detail})

    # Primary keys / composite keys
    key_map = {
        "teams": ["team_id"], "engineers": ["engineer_id"], "sprints": ["sprint_id"],
        "tasks": ["task_id"], "deployments": ["deployment_id"],
        "cloud_costs": ["cost_id"], "incidents": ["incident_id"],
    }
    for table, keys in key_map.items():
        dupes = int(data[table].duplicated(keys).sum())
        add(f"{table} primary key uniqueness", dupes == 0, f"Duplicate key rows: {dupes}")
    dupes = int(data["capacity"].duplicated(["date", "team_id"]).sum())
    add("capacity composite key uniqueness", dupes == 0, f"Duplicate date/team rows: {dupes}")

    team_ids = set(data["teams"]["team_id"])
    engineer_ids = set(data["engineers"]["engineer_id"])
    sprint_ids = set(data["sprints"]["sprint_id"])
    deployment_ids = set(data["deployments"]["deployment_id"])
    for table in ["engineers", "sprints", "tasks", "deployments", "cloud_costs", "capacity", "incidents"]:
        bad = int((~data[table]["team_id"].isin(team_ids)).sum())
        add(f"{table}.team_id foreign key", bad == 0, f"Orphan team references: {bad}")
    bad = int((~data["tasks"]["sprint_id"].isin(sprint_ids)).sum())
    add("tasks.sprint_id foreign key", bad == 0, f"Orphan sprint references: {bad}")
    assigned = data["tasks"]["assignee_id"].dropna()
    bad = int((~assigned.isin(engineer_ids)).sum())
    add("tasks.assignee_id foreign key", bad == 0, f"Orphan non-null engineer references: {bad}")
    bad = int((~data["deployments"]["engineer_id"].isin(engineer_ids)).sum())
    add("deployments.engineer_id foreign key", bad == 0, f"Orphan engineer references: {bad}")
    linked = data["incidents"]["related_deployment_id"].replace("", pd.NA).dropna()
    bad = int((~linked.isin(deployment_ids)).sum())
    add("incidents.related_deployment_id foreign key", bad == 0, f"Orphan linked deployment references: {bad}")

    # Core domain rules
    add("task status values", set(data["tasks"]["status"].dropna().unique()).issubset({"Done", "In Progress", "Blocked", "To Do"}),
        f"Observed: {sorted(data['tasks']['status'].dropna().unique().tolist())}")
    add("deployment status values", set(data["deployments"]["status"].dropna().unique()).issubset({"Success", "Failed"}),
        f"Observed: {sorted(data['deployments']['status'].dropna().unique().tolist())}")
    add("cloud costs positive", bool((data["cloud_costs"]["cost_inr"] > 0).all()),
        f"Minimum cost: {data['cloud_costs']['cost_inr'].min():.2f} INR")
    add("capacity hours non-negative", bool(((data["capacity"]["available_hours"] >= 0) & (data["capacity"]["logged_hours"] >= 0)).all()),
        "Available and logged hours must be non-negative")
    add("sprint dates ordered", bool((data["sprints"]["end_date"] >= data["sprints"]["start_date"]).all()),
        "Every sprint end date must be on or after its start date")
    done = data["tasks"][data["tasks"]["status"].eq("Done")]
    add("completed tasks have completed_at", bool(done["completed_at"].notna().all()),
        f"Completed tasks missing completed_at: {int(done['completed_at'].isna().sum())}")
    add("completed tasks have cycle time", bool(done["cycle_time_days"].notna().all()),
        f"Completed tasks missing cycle_time_days: {int(done['cycle_time_days'].isna().sum())}")
    unresolved = data["incidents"][data["incidents"]["status"].eq("Open")]
    add("open incidents have blank resolved_at", bool(unresolved["resolved_at"].isna().all()),
        f"Open incidents with resolved_at: {int(unresolved['resolved_at'].notna().sum())}")

    # Expected intentional nulls are warnings, not errors.
    null_assignees = int(data["tasks"]["assignee_id"].isna().sum())
    add("unassigned tasks allowed", True, f"Unassigned tasks: {null_assignees}; intentional nullable field", "INFO")
    open_count = int(data["incidents"]["status"].eq("Open").sum())
    add("open incidents retained", True, f"Open/unresolved incidents: {open_count}; excluded from MTTR", "INFO")

    return pd.DataFrame(checks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--output", default="outputs/data_validation_report.csv")
    args = parser.parse_args()
    data = load_data(args.data_dir)
    report = validate(data)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output, index=False)
    print(report.to_string(index=False))
    failures = report[(report["status"] == "FAIL") & (report["severity"] == "ERROR")]
    print(f"\nChecks: {len(report)} | Failures: {len(failures)}")
    if len(failures):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
