"""Interactive Streamlit dashboard for the Engineering Productivity project."""
from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analytics import load_data, run_all_analyses  # noqa: E402

st.set_page_config(
    page_title="Engineering Productivity & Cloud Cost Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Engineering Productivity & Cloud Cost Intelligence")
st.caption("Portfolio analytics dashboard · fictional synthetic dataset · not company or Zepto data")

@st.cache_data(show_spinner="Loading the project data...")
def get_data():
    data = load_data(ROOT / "data" / "raw")
    outputs = run_all_analyses(data)
    return data, outputs

try:
    data, out = get_data()
except Exception as exc:  # surface a useful setup message instead of a blank app
    st.error(f"Could not load project data: {exc}")
    st.info("Run this app from the project root with: streamlit run app/Home.py")
    st.stop()

teams = data["teams"].copy()
team_options = teams["team_name"].tolist()
with st.sidebar:
    st.header("Dashboard filters")
    selected_teams = st.multiselect("Engineering teams", team_options, default=team_options)
    selected_ids = teams.loc[teams["team_name"].isin(selected_teams), "team_id"].tolist()
    st.divider()
    st.caption("Dataset context")
    st.write(f"**Teams:** {len(teams)}")
    st.write(f"**Engineers:** {len(data['engineers'])}")
    st.write(f"**Tasks:** {len(data['tasks']):,}")
    st.write(f"**Date range:** {data['sprints']['start_date'].min().date()} to {data['sprints']['end_date'].max().date()}")
    st.caption("All organizations, people, metrics and costs are simulated for portfolio practice.")

if not selected_ids:
    st.warning("Select at least one team in the sidebar.")
    st.stop()

# Filtered source facts and analytic tables.
tasks = data["tasks"][data["tasks"]["team_id"].isin(selected_ids)].copy()
deployments = data["deployments"][data["deployments"]["team_id"].isin(selected_ids)].copy()
production = deployments[deployments["environment"].eq("Production")].copy()
cloud = data["cloud_costs"][data["cloud_costs"]["team_id"].isin(selected_ids)].copy()
capacity = data["capacity"][data["capacity"]["team_id"].isin(selected_ids)].copy()
incidents = data["incidents"][data["incidents"]["team_id"].isin(selected_ids)].copy()

team_task = out["team_task_summary"][out["team_task_summary"]["team_id"].isin(selected_ids)]
sprint_kpis = out["sprint_kpis_by_team_sprint"][out["sprint_kpis_by_team_sprint"]["team_id"].isin(selected_ids)]
deploy_month = out["production_deployments_by_team_month"][out["production_deployments_by_team_month"]["team_id"].isin(selected_ids)]
cloud_month = out["cloud_cost_by_team_month"][out["cloud_cost_by_team_month"]["team_id"].isin(selected_ids)]
cloud_service = out["cloud_cost_by_service_environment"][out["cloud_cost_by_service_environment"]["team_id"].isin(selected_ids)]
capacity_team = out["capacity_team_summary"][out["capacity_team_summary"]["team_id"].isin(selected_ids)]
capacity_month = out["capacity_by_team_month"][out["capacity_by_team_month"]["team_id"].isin(selected_ids)]
incident_severity = out["incidents_by_team_severity"][out["incidents_by_team_severity"]["team_id"].isin(selected_ids)]
backlog = out["backlog_as_of_dataset_end"][out["backlog_as_of_dataset_end"]["team_id"].isin(selected_ids)]

# Top-level KPIs are recalculated from filtered underlying facts.
committed = tasks.loc[tasks["is_committed"]]
completed_committed = committed.loc[committed["status"].eq("Done")]
commit_pct = (100 * completed_committed["story_points"].sum() / committed["story_points"].sum()) if committed["story_points"].sum() else 0
prod_fail_pct = (100 * production["status"].eq("Failed").mean()) if len(production) else 0
cloud_actual = float(cloud["cost_inr"].sum())
cloud_budget = float(cloud["budget_inr"].sum())
cloud_var_pct = (100 * (cloud_actual / cloud_budget - 1)) if cloud_budget else 0
util_pct = (100 * capacity["logged_hours"].sum() / capacity["available_hours"].sum()) if capacity["available_hours"].sum() else 0
resolved = incidents.dropna(subset=["resolved_at"]).copy()
resolved["mttr_hours"] = (pd.to_datetime(resolved["resolved_at"]) - pd.to_datetime(resolved["started_at"])).dt.total_seconds() / 3600
mttr = float(resolved["mttr_hours"].mean()) if len(resolved) else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Committed point completion", f"{commit_pct:.1f}%")
k2.metric("Production deployment failures", f"{prod_fail_pct:.1f}%")
k3.metric("Cloud spend", f"₹{cloud_actual/100000:.2f}L", f"{cloud_var_pct:+.1f}% vs allocated budget")
k4.metric("Weighted utilization", f"{util_pct:.1f}%")
k5.metric("Resolved incident MTTR", f"{mttr:.2f} hrs")

st.caption("Metrics update when you change the team filter. Percentages use weighted denominators rather than unweighted averages of team percentages.")

tab_overview, tab_sprint, tab_deploy, tab_cloud, tab_capacity, tab_reliability = st.tabs([
    "Executive overview", "Sprint productivity", "Deployments", "Cloud costs", "Capacity", "Reliability"
])

with tab_overview:
    left, right = st.columns(2)
    with left:
        chart = team_task.sort_values("commit_completion_pct", ascending=False)
        fig = px.bar(chart, x="team_name", y="commit_completion_pct", color="commit_completion_pct",
                     title="Committed story-point completion by team", labels={"team_name": "Team", "commit_completion_pct": "Completion (%)"})
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(capacity_team.sort_values("utilization_pct", ascending=False), x="team_name", y="utilization_pct",
                     title="Weighted resource utilization by team", labels={"team_name": "Team", "utilization_pct": "Utilization (%)"})
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Team scorecard")
    scorecard = (team_task[["team_id", "team_name", "headcount", "task_count", "task_completion_pct", "commit_completion_pct", "mean_cycle_time_days"]]
        .merge(out["production_deployment_team_summary"][["team_id", "production_deployments", "failure_rate_pct"]], on="team_id", how="left")
        .merge(capacity_team[["team_id", "utilization_pct"]], on="team_id", how="left"))
    st.dataframe(scorecard.round(2), use_container_width=True, hide_index=True)

with tab_sprint:
    left, right = st.columns(2)
    with left:
        fig = px.line(sprint_kpis, x="sprint_number", y="commit_completion_pct", color="team_name", markers=True,
                      title="Sprint commitment completion trend", labels={"sprint_number": "Sprint", "commit_completion_pct": "Completion (%)", "team_name": "Team"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        status = tasks.groupby(["team_id", "status"], as_index=False).size().merge(teams[["team_id", "team_name"]], on="team_id")
        fig = px.bar(status, x="team_name", y="size", color="status", barmode="stack",
                     title="Work-item status mix", labels={"team_name": "Team", "size": "Tasks"})
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Longest open work items")
    cols = ["task_id", "team_name", "task_type", "priority", "status", "age_days_as_of_dataset_end", "blocked_days"]
    st.dataframe(backlog[cols].head(25), use_container_width=True, hide_index=True)
    st.caption("Backlog ageing is calculated as at the final sprint end date in the synthetic dataset, not today's date.")

with tab_deploy:
    if production.empty:
        st.info("No production deployment records for the selected teams.")
    else:
        left, right = st.columns(2)
        with left:
            fig = px.line(deploy_month, x="month", y="production_deployments", color="team_name", markers=True,
                          title="Production deployment volume by month", labels={"month": "Month", "production_deployments": "Deployments"})
            st.plotly_chart(fig, use_container_width=True)
        with right:
            deploy_summary = out["production_deployment_team_summary"].query("team_id in @selected_ids")
            fig = px.bar(deploy_summary.sort_values("failure_rate_pct", ascending=False), x="team_name", y="failure_rate_pct",
                         title="Production deployment failure rate", labels={"team_name": "Team", "failure_rate_pct": "Failure rate (%)"})
            fig.update_layout(xaxis_tickangle=-25)
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("Monthly deployment scorecard")
        st.dataframe(deploy_month.round(2), use_container_width=True, hide_index=True)
        st.caption("Failure rate = failed Production deployments / all Production deployments. Staging and Development are excluded.")

with tab_cloud:
    left, right = st.columns(2)
    with left:
        fig = px.line(cloud_month, x="month", y="actual_cost_inr", color="team_name", markers=True,
                      title="Monthly cloud expenditure", labels={"month": "Month", "actual_cost_inr": "Cost (INR)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.bar(cloud_service.sort_values("actual_cost_inr", ascending=False).head(15),
                     x="service_name", y="actual_cost_inr", color="environment",
                     title="Top service / environment cost combinations", labels={"service_name": "Service", "actual_cost_inr": "Cost (INR)"})
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Team-month budget variance")
    st.dataframe(cloud_month.round(2), use_container_width=True, hide_index=True)
    st.caption("Budget is a simulated daily allocation, not an actual cloud invoice. Investigate outliers before recommending spend cuts.")

with tab_capacity:
    left, right = st.columns(2)
    with left:
        fig = px.line(capacity_month, x="month", y="utilization_pct", color="team_name", markers=True,
                      title="Monthly weighted resource utilization", labels={"month": "Month", "utilization_pct": "Utilization (%)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        mix = capacity_team.melt(id_vars=["team_name"], value_vars=["delivery_hours", "support_hours", "incident_hours", "meeting_and_admin_hours"],
                                 var_name="work_type", value_name="hours")
        fig = px.bar(mix, x="team_name", y="hours", color="work_type", title="Recorded work-hour mix",
                     labels={"team_name": "Team", "hours": "Hours", "work_type": "Work type"})
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Capacity detail")
    st.dataframe(capacity_team.round(2), use_container_width=True, hide_index=True)
    st.caption("Utilization can exceed 100% when logged hours exceed available hours due to simulated overtime. High utilization is not inherently good.")

with tab_reliability:
    left, right = st.columns(2)
    with left:
        fig = px.bar(incident_severity, x="severity", y="incident_count", color="team_name", barmode="group",
                     title="Incident count by severity and team", labels={"incident_count": "Incidents", "severity": "Severity"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        mttr_df = incident_severity.dropna(subset=["mean_mttr_hours"])
        fig = px.bar(mttr_df, x="severity", y="mean_mttr_hours", color="team_name", barmode="group",
                     title="Mean time to restore by severity", labels={"mean_mttr_hours": "Mean MTTR (hours)", "severity": "Severity"})
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Incident records")
    incident_view = incidents.copy()
    incident_view["started_at"] = pd.to_datetime(incident_view["started_at"])
    st.dataframe(incident_view.sort_values("started_at", ascending=False), use_container_width=True, hide_index=True)
    st.caption("Unresolved incidents are excluded from MTTR. A linked deployment is a simulated triage association, not proof of causation.")

st.divider()
st.caption("Portfolio demonstration only · Synthetic data · No affiliation with or internal data from Zepto")
