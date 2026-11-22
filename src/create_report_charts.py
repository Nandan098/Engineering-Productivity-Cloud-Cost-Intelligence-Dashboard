"""Create static PNG exhibits for the portfolio readout."""
from pathlib import Path
import sys
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from analytics import load_data, run_all_analyses


def main() -> None:
    data = load_data(ROOT / "data" / "raw")
    out = run_all_analyses(data)
    fig_dir = ROOT / "reports" / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Committed story-point completion by team.
    d = out["team_task_summary"].sort_values("commit_completion_pct")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(d["team_name"], d["commit_completion_pct"])
    ax.set_title("Committed story-point completion by team")
    ax.set_xlabel("Completion (%)")
    ax.set_ylabel("Engineering team")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(fig_dir / "committed_completion_by_team.png", dpi=160)
    plt.close(fig)

    # 2. Production deployment failure rate alongside total deployment count.
    d = out["production_deployment_team_summary"].sort_values("failure_rate_pct")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(d["team_name"], d["failure_rate_pct"])
    ax.set_title("Production deployment failure rate by team")
    ax.set_xlabel("Failure rate (%)")
    ax.set_ylabel("Engineering team")
    ax.grid(axis="x", alpha=0.25)
    for bar, count in zip(bars, d["production_deployments"]):
        ax.text(bar.get_width() + 0.25, bar.get_y() + bar.get_height()/2,
                f"{bar.get_width():.1f}%  (n={int(count)})", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "production_deployment_failure_rate.png", dpi=160)
    plt.close(fig)

    # 3. Monthly cloud cost vs allocated budget.
    d = out["cloud_cost_by_team_month"].groupby("month", as_index=False).agg(
        actual_cost_inr=("actual_cost_inr", "sum"), budget_inr=("budget_inr", "sum")
    )
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(d["month"], d["actual_cost_inr"], marker="o", label="Actual simulated cost")
    ax.plot(d["month"], d["budget_inr"], marker="o", label="Allocated simulated budget")
    ax.set_title("Monthly cloud cost vs allocated budget")
    ax.set_xlabel("Month")
    ax.set_ylabel("INR")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "cloud_cost_vs_budget.png", dpi=160)
    plt.close(fig)

    # 4. Weighted resource utilization.
    d = out["capacity_team_summary"].sort_values("utilization_pct")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(d["team_name"], d["utilization_pct"])
    ax.axvline(100, linestyle="--", linewidth=1, label="100% of available hours")
    ax.set_title("Weighted resource utilization by team")
    ax.set_xlabel("Logged hours / available hours (%)")
    ax.set_ylabel("Engineering team")
    ax.grid(axis="x", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "resource_utilization_by_team.png", dpi=160)
    plt.close(fig)

    print(f"Created four charts in {fig_dir}")

if __name__ == "__main__":
    main()
