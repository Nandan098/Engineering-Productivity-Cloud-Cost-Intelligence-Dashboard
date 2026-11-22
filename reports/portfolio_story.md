# Portfolio walkthrough and interview talking points

## 45-second project explanation

“I built an end-to-end engineering analytics project using a fictional synthetic dataset. The goal was to help engineering managers monitor sprint commitment completion, production deployment reliability, cloud expenditure and team capacity. I validated eight linked datasets in Python, created PostgreSQL tables and business queries, generated analysis-ready KPI tables, and built an interactive Streamlit dashboard. I also prepared a Power BI model guide and DAX measures so the same data can be explored in Power BI.”

## Three data-supported observations to discuss

These are descriptive findings from this synthetic dataset only. They are not Zepto results or industry benchmarks.

1. **Sprint delivery:** Core Platform has the highest committed story-point completion (83.5%) and Fulfillment Systems the lowest (70.5%). A sensible next step is to compare sprint scope, support load, blocked work and estimation practices before recommending any process change.
2. **Release reliability:** Merchant Integrations records a 14.3% production deployment failure rate (3 failed out of 21), while SRE & Infrastructure records 2.8% (2 out of 71). Always state the numerator and denominator. The smaller event count makes Merchant Integrations' rate more volatile; inspect service and release-level details before drawing conclusions.
3. **Capacity and cloud costs:** SRE & Infrastructure has 92.3% weighted logged-hours utilization. This should trigger a capacity-buffer and overtime review, not a “highest is best” conclusion. Overall simulated cloud spend is about 15.0% below the allocated budget; the useful question is whether the allocation assumptions reflect real usage, not how to cut spend automatically.

## Recommended demo sequence

1. Start with the README and explain the synthetic-data disclaimer.
2. Show `outputs/data_validation_report.csv` and explain primary keys / foreign-key checks.
3. Open `sql/03_analysis_queries.sql`; walk through sprint completion or production deployment failure rate.
4. Launch the Streamlit dashboard and use the team filter.
5. Open `reports/management_readout.md` and explain one metric, denominator, caveat and follow-up action.
6. Explain how you would replace the CSV layer with approved production data and schedule a controlled refresh.

## Questions an interviewer may ask

**Why did you use weighted utilization?**

It is calculated as total logged hours divided by total available hours. This is more appropriate than taking an unweighted average of daily or team percentages when denominators differ. It still needs interpretation: logged time is not the same as productive output, and high utilization can signal overload.

**Why compare sprint completion rather than raw velocity across teams?**

Story points are team-relative estimates. Completion against each team's own committed points is a more defensible delivery-predictability indicator than comparing raw point totals across teams.

**How did you treat open incidents?**

I keep them visible as open incidents but exclude them from MTTR, because there is no resolution timestamp yet.

**Can you conclude deployments caused incidents?**

No. The related deployment field is a synthetic triage association. Temporal association is a lead for investigation, not evidence of causation.

**Are the costs actual vendor bills?**

No. They are simulated actual-cost records compared with illustrative daily budget allocations. The data is for practicing cost variance analysis, not financial reporting.

**What would you do next in a real business?**

Confirm KPI definitions with engineering leadership, validate data lineage and source-system fields, agree access controls, compare with a trusted baseline, and pilot a recurring dashboard with owners for every metric and alert.

## Do not overclaim

- Do not say this project reduced cloud costs, improved delivery or reduced incidents: it analyses synthetic data and does not implement changes in a real operation.
- Do not call this Zepto data.
- Do not claim causal explanations from descriptive correlations.
- Only list tools you have personally run and can explain in an interview.
