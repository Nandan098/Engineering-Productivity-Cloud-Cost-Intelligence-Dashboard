# Analysis summary

> **Synthetic portfolio dataset only.** These are calculations from the fictional dataset in `data/raw/`, not facts about Zepto or any real organization. Observations are descriptive, not causal.

## Overall snapshot

- Dataset cut-off date for backlog age: **2026-11-01**.
- Work items marked Done: **79.4%** of all tasks.
- Overall committed story-point completion: **76.9%**.
- Production deployment failure rate: **6.7%** (failed production deployments / all production deployments).
- Cloud actual spend vs allocated budget: **₹8,372,287** vs **₹9,854,691**, or **-15.0%** variance.
- Weighted logged-hours utilization: **84.6%** (sum of logged hours / sum of available hours).
- Mean time to restore among resolved incidents: **3.32 hours**; unresolved incidents are excluded.

## Team-level observations to investigate

1. **Committed work completion:** Core Platform has the highest team-level committed story-point completion (**83.5%**), while Fulfillment Systems has the lowest (**70.5%**). Compare task mix, support load, sprint scope and team size before interpreting this as performance.
2. **Production deployment reliability:** Merchant Integrations has the highest production deployment failure rate (**14.3%**); SRE & Infrastructure has the lowest (**2.8%**). Review deployment counts as well as rates because small denominators can make percentages volatile.
3. **Cloud spend:** Core Platform has the highest aggregate cloud cost (**₹1,676,573**). Consumer Mobile has the smallest underspend relative to its allocated daily budget (**-14.4%**, closest to the allocated amount). All teams are below their simulated allocation in this dataset. Absolute spend and budget variance are different questions and should not be conflated.
4. **Capacity:** SRE & Infrastructure has the highest weighted utilization (**92.3%**). Sustained high utilization may indicate reduced slack or overload; it is not automatically a positive outcome.
5. **Cycle time:** Core Platform has the longest average completed-task cycle time (**5.44 days**). Compare similar work types and sizes before proposing changes.

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
