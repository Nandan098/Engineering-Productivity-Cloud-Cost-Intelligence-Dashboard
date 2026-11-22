"""Validate input data and write reproducible analysis outputs and a summary report."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from analytics import load_data, run_all_analyses, data_as_of_date
from validate_data import validate


def write_summary(data: dict, outputs: dict[str, pd.DataFrame], report_path: Path) -> None:
    teams = data["teams"].copy()
    task = outputs["team_task_summary"].copy()
    deploy = outputs["production_deployment_team_summary"].copy()
    cloud = data["cloud_costs"].groupby("team_id", as_index=False).agg(actual=("cost_inr", "sum"), budget=("budget_inr", "sum"))
    cloud["variance_pct"] = 100 * (cloud["actual"] - cloud["budget"]) / cloud["budget"]
    cap = outputs["capacity_team_summary"][["team_id", "utilization_pct"]]
    incidents = outputs["incident_team_summary"]
    summary = (teams[["team_id", "team_name", "headcount"]]
        .merge(task[["team_id", "task_count", "task_completion_pct", "commit_completion_pct", "mean_cycle_time_days"]], on="team_id")
        .merge(deploy[["team_id", "production_deployments", "failure_rate_pct", "rollback_rate_pct"]], on="team_id")
        .merge(cloud[["team_id", "actual", "budget", "variance_pct"]], on="team_id")
        .merge(cap, on="team_id")
        .merge(incidents[["team_id", "incident_count", "open_incidents", "mean_mttr_hours"]], on="team_id"))
    summary.to_csv(report_path.parent / "team_scorecard.csv", index=False)

    task_done = float((data["tasks"]["status"] == "Done").mean() * 100)
    total_actual = float(data["cloud_costs"]["cost_inr"].sum())
    total_budget = float(data["cloud_costs"]["budget_inr"].sum())
    budget_variance = (total_actual / total_budget - 1) * 100
    total_prod = data["deployments"].query("environment == 'Production'")
    prod_failure = float((total_prod["status"] == "Failed").mean() * 100)
    overall_util = float(data["capacity"]["logged_hours"].sum() / data["capacity"]["available_hours"].sum() * 100)
    resolved = data["incidents"].dropna(subset=["resolved_at"]).copy()
    resolved["mttr_hours"] = (resolved["resolved_at"] - resolved["started_at"]).dt.total_seconds() / 3600
    mttr = float(resolved["mttr_hours"].mean())

    best_commit = summary.loc[summary["commit_completion_pct"].idxmax()]
    low_commit = summary.loc[summary["commit_completion_pct"].idxmin()]
    high_failure = summary.loc[summary["failure_rate_pct"].idxmax()]
    low_failure = summary.loc[summary["failure_rate_pct"].idxmin()]
    high_util = summary.loc[summary["utilization_pct"].idxmax()]
    highest_spend = summary.loc[summary["actual"].idxmax()]
    biggest_over = summary.loc[summary["variance_pct"].idxmax()]
    worst_cycle = summary.loc[summary["mean_cycle_time_days"].idxmax()]

    text = f"""# Analysis summary

> **Synthetic portfolio dataset only.** These are calculations from the fictional dataset in `data/raw/`, not facts about Zepto or any real organization. Observations are descriptive, not causal.

## Overall snapshot

- Dataset cut-off date for backlog age: **{data_as_of_date(data).date()}**.
- Work items marked Done: **{task_done:.1f}%** of all tasks.
- Overall committed story-point completion: **{100 * data['tasks'].loc[data['tasks']['is_committed'] & data['tasks']['status'].eq('Done'), 'story_points'].sum() / max(data['tasks'].loc[data['tasks']['is_committed'], 'story_points'].sum(), 1):.1f}%**.
- Production deployment failure rate: **{prod_failure:.1f}%** (failed production deployments / all production deployments).
- Cloud actual spend vs allocated budget: **₹{total_actual:,.0f}** vs **₹{total_budget:,.0f}**, or **{budget_variance:+.1f}%** variance.
- Weighted logged-hours utilization: **{overall_util:.1f}%** (sum of logged hours / sum of available hours).
- Mean time to restore among resolved incidents: **{mttr:.2f} hours**; unresolved incidents are excluded.

## Team-level observations to investigate

1. **Committed work completion:** {best_commit['team_name']} has the highest team-level committed story-point completion (**{best_commit['commit_completion_pct']:.1f}%**), while {low_commit['team_name']} has the lowest (**{low_commit['commit_completion_pct']:.1f}%**). Compare task mix, support load, sprint scope and team size before interpreting this as performance.
2. **Production deployment reliability:** {high_failure['team_name']} has the highest production deployment failure rate (**{high_failure['failure_rate_pct']:.1f}%**); {low_failure['team_name']} has the lowest (**{low_failure['failure_rate_pct']:.1f}%**). Review deployment counts as well as rates because small denominators can make percentages volatile.
3. **Cloud spend:** {highest_spend['team_name']} has the highest aggregate cloud cost (**₹{highest_spend['actual']:,.0f}**). {biggest_over['team_name']} has the smallest underspend relative to its allocated daily budget (**{biggest_over['variance_pct']:+.1f}%**, closest to the allocated amount). All teams are below their simulated allocation in this dataset. Absolute spend and budget variance are different questions and should not be conflated.
4. **Capacity:** {high_util['team_name']} has the highest weighted utilization (**{high_util['utilization_pct']:.1f}%**). Sustained high utilization may indicate reduced slack or overload; it is not automatically a positive outcome.
5. **Cycle time:** {worst_cycle['team_name']} has the longest average completed-task cycle time (**{worst_cycle['mean_cycle_time_days']:.2f} days**). Compare similar work types and sizes before proposing changes.

## Recommended management questions

- Are sprint commitments being made using historical capacity and support demand?
- Which cost services contribute most to total spend, and which day-level records are genuine outliers?
- Are deployment failures concentrated in a small number of services, environments or release windows?
- Is utilization consistently high, and does it coincide with increased task ageing or incident load?
- Which blocked work items are oldest, and what dependency or ownership change would unblock them?

## Interpretation limits

- Story points are team-relative and must not be used as a standardized cross-team productivity measure.
- The deployment-to-incident association column is simulated triage metadata, not causal proof.
- Budget values are illustrative daily allocations, not vendor invoices.
- Team and individual results are fictional and should not be represented as real-world benchmarks.
"""
    report_path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/raw")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_data(args.data_dir)
    validation = validate(data)
    validation.to_csv(output_dir / "data_validation_report.csv", index=False)
    failures = validation[(validation["status"] == "FAIL") & (validation["severity"] == "ERROR")]
    if len(failures):
        print(validation.to_string(index=False))
        raise SystemExit("Data validation failed. Resolve errors before analysis.")

    tables = run_all_analyses(data)
    for name, df in tables.items():
        df.to_csv(output_dir / f"{name}.csv", index=False)
    write_summary(data, tables, output_dir / "analysis_summary.md")
    print(f"Validation passed ({len(validation)} checks). Wrote {len(tables)} analysis tables to {output_dir.resolve()}.")

if __name__ == "__main__":
    main()
