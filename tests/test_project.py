from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analytics import load_data, run_all_analyses
from validate_data import validate


def get_data():
    return load_data(ROOT / "data" / "raw")


def test_expected_tables_and_record_counts():
    data = get_data()
    assert len(data["teams"]) == 7
    assert len(data["engineers"]) == 50
    assert len(data["tasks"]) == 939
    assert len(data["deployments"]) == 684
    assert len(data["cloud_costs"]) == 19110
    assert len(data["capacity"]) == 910
    assert len(data["incidents"]) == 148


def test_foreign_keys_and_validation():
    report = validate(get_data())
    failures = report[(report["status"] == "FAIL") & (report["severity"] == "ERROR")]
    assert failures.empty, failures.to_string(index=False)


def test_analytics_have_expected_outputs_and_valid_denominators():
    data = get_data()
    out = run_all_analyses(data)
    expected = {
        "sprint_kpis_by_team_sprint", "team_task_summary", "backlog_as_of_dataset_end",
        "production_deployments_by_team_month", "production_deployment_team_summary",
        "cloud_cost_by_team_month", "cloud_cost_by_service_environment", "cloud_cost_detail",
        "capacity_by_team_month", "capacity_team_summary", "incidents_by_team_severity",
        "incident_team_summary", "task_type_summary",
    }
    assert expected.issubset(out.keys())
    assert out["sprint_kpis_by_team_sprint"]["commit_completion_pct"].dropna().between(0, 100).all()
    assert out["production_deployment_team_summary"]["failure_rate_pct"].between(0, 100).all()
    assert out["capacity_team_summary"]["utilization_pct"].gt(0).all()
    assert out["backlog_as_of_dataset_end"]["status"].ne("Done").all()


def test_incident_mttr_excludes_unresolved_incidents():
    data = get_data()
    out = run_all_analyses(data)
    severity = out["incidents_by_team_severity"]
    assert severity["mean_mttr_hours"].notna().all()
    assert data["incidents"].loc[data["incidents"]["status"].eq("Open"), "resolved_at"].isna().all()
