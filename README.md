# Engineering Productivity & Cloud Cost Intelligence

**End-to-end Business Analyst portfolio project** built with Python, SQL, Power BI and Streamlit.

> **Data notice:** This project uses fictional synthetic data. It is not Zepto data, is not based on any internal Zepto system, and must not be represented as real company metrics. The fictional teams, people, engineering events and costs exist only for portfolio practice.

## Business problem

Engineering leaders need a consistent view of delivery predictability, deployment reliability, cloud expenditure and engineering capacity. This project builds an analytics workflow that transforms raw operational records into SQL analyses, executive KPIs, a five-area interactive dashboard and management questions.

## What the project delivers

- **Python data validation:** unique keys, referential integrity, date and status rules, and explicit treatment of intentional nulls.
- **Exploratory / KPI analysis:** sprint commitment completion, task status and cycle time, production deployment reliability, cloud cost variance, weighted capacity utilization, incident MTTR and backlog ageing.
- **SQL analysis:** PostgreSQL schema, CSV load script and ten reusable business queries.
- **Interactive dashboard:** Streamlit application with team filters and six tabs (overview, sprint productivity, deployments, cloud costs, capacity and reliability).
- **Power BI handoff:** relationship design, report-page plan and DAX measures so the same CSVs can be imported into Power BI Desktop.
- **Interview preparation:** a management readout and project walkthrough talking points grounded in the generated results.
- **Portfolio documentation:** data dictionary, KPI definitions, assumptions, analytical cautions and a generated scorecard.

## Dataset profile

| Dataset | Records |
|---|---:|
| Engineering teams | 7 |
| Engineers | 50 |
| Team-specific sprint cycles | 91 |
| Engineering tasks | 939 |
| Deployment events | 684 |
| Daily cloud cost lines | 19,110 |
| Team-day capacity rows | 910 |
| Production / operational incidents | 148 |

Coverage: May 4, 2026 to November 1, 2026 for the sprint and team-day data. Some task creation timestamps precede the sprint window because committed work can be created during pre-sprint planning.

The records are deliberately non-uniform: teams have different headcounts, workloads, work mixes, sprint outcomes, deployment cadences, service costs, capacity patterns and incident volumes. This gives the analysis realistic variation, but the simulated data is not statistically representative of any real organization.

## Folder structure

```text
Engineering_Productivity_Cloud_Cost_Analytics/
├── app/
│   └── Home.py                         # Interactive Streamlit dashboard
├── data/
│   └── raw/                            # Eight linked CSV source tables
├── docs/
│   ├── data_dictionary.csv
│   ├── data_model.md
│   ├── field_level_data_dictionary.md
│   └── ORIGINAL_DATASET_README.md
├── notebooks/
│   └── 01_exploratory_analysis.ipynb    # Guided EDA notebook
├── outputs/                            # Generated CSV analyses and scorecard
├── powerbi/
│   ├── DAX_Measures.dax
│   └── Model_Guide.md
├── reports/
│   ├── figures/                         # Static chart exhibits
│   ├── management_readout.md
│   └── portfolio_story.md
├── sql/
│   ├── 01_schema_postgresql.sql
│   ├── 02_load_csvs.psql
│   └── 03_analysis_queries.sql
├── src/
│   ├── analytics.py
│   ├── run_analysis.py
│   └── validate_data.py
├── tests/
│   └── test_project.py
├── requirements.txt
├── Makefile
├── LICENSE
└── README.md
```

## Quick start: run locally

### 1. Extract and open the project

Extract the ZIP and open a terminal in the project folder (the folder containing this README).

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Validate the raw data

```bash
python src/validate_data.py
```

This creates `outputs/data_validation_report.csv`. The script exits with an error if a critical validation check fails. Unassigned task assignees and unresolved incident end-times are intentional and documented.

### 4. Run the analytics pipeline

```bash
python src/run_analysis.py
```

This writes analysis-ready tables to `outputs/`, including:

- `sprint_kpis_by_team_sprint.csv`
- `team_task_summary.csv`
- `backlog_as_of_dataset_end.csv`
- `production_deployments_by_team_month.csv`
- `production_deployment_team_summary.csv`
- `cloud_cost_by_team_month.csv`
- `cloud_cost_by_service_environment.csv`
- `capacity_by_team_month.csv`
- `capacity_team_summary.csv`
- `incidents_by_team_severity.csv`
- `incident_team_summary.csv`
- `task_type_summary.csv`
- `team_scorecard.csv`
- `analysis_summary.md`

### 5. Launch the interactive dashboard

```bash
streamlit run app/Home.py
```

Streamlit will print a local URL (commonly `http://localhost:8501`). Open it in your browser. Select one or more teams in the sidebar to filter the dashboard.

### 6. Run tests

```bash
pytest -q
```

## Static report exhibits

Four static chart PNGs are saved in `reports/figures/` for a portfolio README or presentation: committed completion, production deployment failure rate (with denominators), cloud cost versus allocated budget, and weighted resource utilization. Recreate them with `python src/create_report_charts.py`.

## PostgreSQL workflow

The Python dashboard and pipeline work directly from CSVs, so a database is not required to run them. To demonstrate SQL as well:

1. Create a PostgreSQL database, for example `engineering_analytics`.
2. From the project root, run:

```bash
psql -d engineering_analytics -f sql/01_schema_postgresql.sql
psql -d engineering_analytics -f sql/02_load_csvs.psql
```

3. Open `sql/03_analysis_queries.sql` in pgAdmin or `psql` and run individual queries.

The second file uses PostgreSQL `\copy` client commands and expects paths relative to the project root. If your database client is not `psql`, import the CSVs using its import wizard and preserve the table/column names.

## Power BI workflow

The CSV dataset can be loaded directly into Power BI Desktop. Follow `powerbi/Model_Guide.md` to create dimension-to-fact relationships, add date fields and assemble report pages. Copy the measures from `powerbi/DAX_Measures.dax` into Power BI's measure editor.

This ZIP includes Power BI source data, model instructions and DAX measures, **not a prebuilt `.pbix` file**. The Streamlit dashboard is the runnable interactive dashboard included in the project.

## KPI definitions

| KPI | Definition |
|---|---|
| Sprint commitment completion | Completed story points for committed tasks / committed story points |
| Production deployment failure rate | Failed Production deployments / all Production deployments |
| Rollback rate | Production deployments with rollback flag / all Production deployments |
| Cloud cost variance | (Actual cloud cost − allocated budget) / allocated budget |
| Weighted resource utilization | Sum of logged hours / sum of available hours |
| MTTR | Mean resolved_at − started_at for resolved incidents, in hours |
| Task cycle time | Mean cycle_time_days for completed tasks |

## Important analytical cautions

1. **Story points are team-relative.** Use trends within a team; do not rank teams by raw velocity as though points were standardized.
2. **Utilization is not a productivity score.** Sustained high utilization can signal overload or insufficient buffer.
3. **Deployment / incident proximity is not causation.** An incident's related deployment field is simulated triage metadata only.
4. **MTTR excludes unresolved incidents.** Keep open incidents visible separately.
5. **Cloud budget is illustrative.** The allocated daily amount is not an invoice, contract or verified vendor spend.
6. **Compare like with like.** Consider team size, service criticality, work type, task size and support load.
7. **Synthetic data is for demonstrating analytical method.** Do not claim the findings describe Zepto or any real business.

## Suggested portfolio walkthrough (3–5 minutes)

1. State the fictional business problem and explain the synthetic-data disclaimer.
2. Show the relational data model and validation report.
3. Demonstrate one SQL query: sprint commitment completion or production deployment failure rate.
4. Open the dashboard and filter to a team.
5. Explain one observation, the denominator behind it, one caveat and a business recommendation to investigate.
6. Close with how the analysis could be refreshed with approved operational data in a real organization.

## Resume usage

Only list technologies and tasks you have personally run and can explain. A truthful description could say you built an end-to-end analytics project using synthetic engineering operations data, Python, SQL and an interactive dashboard. Do not claim cost savings or operational improvements unless you have calculated and clearly labelled a defensible scenario estimate.
