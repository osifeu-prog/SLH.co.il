#!/usr/bin/env python3
"""
SLH Dynamic Yield — Treasury Simulation

Run 12-month stress tests on the Dynamic Yield economic model across
4 scenarios: Bear, Base, Bull, Crisis. Outputs CSV + matplotlib charts
showing Buffer, CR, implied APY, and Circuit Breaker activation timeline.

Companion to Academia Course #1, Module 5.

Usage:
    python treasury_simulation.py --scenario base --tvl 500000 --months 12
    python treasury_simulation.py --scenario crisis --tvl 500000
    python treasury_simulation.py --all  # run all 4 scenarios, side-by-side

Requires: numpy, matplotlib (pip install numpy matplotlib)
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import numpy as np
except ImportError:
    print("Missing numpy. Install with: pip install numpy")
    sys.exit(1)


# ============================================================
# Economic Model
# ============================================================

@dataclass
class PeriodState:
    """State of the system at the start of a single period (month)."""
    month: int
    U: float       # TVL
    B: float       # Buffer
    L: float       # Liquid assets
    R: float       # Revenue this period
    C: float       # Costs this period
    Ref: float     # Referral payouts this period
    W: float       # Withdrawals this period
    k: float       # Distribution coefficient


@dataclass
class PeriodResult:
    """Calculated results for a period after running formulas + breakers."""
    month: int
    U_start: float
    U_end: float
    B_start: float
    B_end: float
    R: float
    C: float
    Ref: float
    Net: float
    P: float           # pool distributed
    CR: float
    implied_APY: float
    W: float
    buffer_ratio: float
    run_threshold: float
    active_breakers: List[str] = field(default_factory=list)
    k_adjusted: float = 0.0
    notes: str = ""


def evaluate_breakers(state: PeriodState, net: float, pool: float) -> Tuple[List[str], float]:
    """Return (active_breakers, adjusted_k).

    Mirrors the logic in modules 3-5 of Course #1.
    """
    active: List[str] = []
    k_adj = state.k

    denom = pool + state.W
    cr = ((net + state.B) / denom) if denom > 0 else float("inf")
    buffer_ratio = state.B / state.U if state.U > 0 else 0
    withdrawal_ratio = state.W / state.U if state.U > 0 else 0

    # Breaker 1: Coverage Guardrail
    if cr < 1.0:
        active.append("COVERAGE_GUARDRAIL")
        k_adj = k_adj * 0.8

    # Breaker 2: Withdrawal Throttle (symbolic — simulation doesn't throttle at daily level)
    if withdrawal_ratio > 0.15:
        active.append("WITHDRAWAL_THROTTLE")

    # Breaker 3: Deposit Freeze
    if cr < 0.5:
        active.append("DEPOSIT_FREEZE")

    # Breaker 4: Buffer Recovery
    if buffer_ratio < 0.10:
        active.append("BUFFER_RECOVERY")
        k_adj = 0.0  # 100% to buffer

    return active, k_adj


def calculate_period(state: PeriodState) -> PeriodResult:
    """Run a single period through the Dynamic Yield formulas + breakers."""
    net = max(0.0, state.R - state.C - state.Ref)
    pool_raw = state.k * net

    active, k_adj = evaluate_breakers(state, net, pool_raw)
    pool_actual = k_adj * net

    denom = pool_actual + state.W
    cr = ((net + state.B) / denom) if denom > 0 else float("inf")
    implied_apy = ((pool_actual / state.U) * 12) if state.U > 0 else 0

    # Buffer evolves: +(Net - Pool_actual) - (withdrawals not covered by revenue)
    withdrawal_gap = max(0.0, state.W - net)
    buffer_delta = (net - pool_actual) - withdrawal_gap
    B_end = max(0.0, state.B + buffer_delta)

    # TVL evolves: -W (withdrawals reduce TVL directly)
    U_end = max(0.0, state.U - state.W)

    buffer_ratio = state.B / state.U if state.U > 0 else 0
    run_threshold = state.L / state.U if state.U > 0 else 0

    return PeriodResult(
        month=state.month,
        U_start=state.U,
        U_end=U_end,
        B_start=state.B,
        B_end=B_end,
        R=state.R,
        C=state.C,
        Ref=state.Ref,
        Net=net,
        P=pool_actual,
        CR=cr if cr != float("inf") else 999.0,
        implied_APY=implied_apy,
        W=state.W,
        buffer_ratio=buffer_ratio,
        run_threshold=run_threshold,
        active_breakers=active,
        k_adjusted=k_adj,
    )


# ============================================================
# Scenario Definitions
# ============================================================

def scenario_base(month: int, tvl: float, rng: np.random.Generator) -> Dict[str, float]:
    """Stable growth, normal operations."""
    r_base = tvl * 0.025  # 2.5% monthly revenue yield
    return {
        "R": r_base * (1 + rng.normal(0, 0.15)),
        "C": tvl * 0.008 + 3000,  # 0.8% + fixed 3K
        "Ref": r_base * 0.15,       # 15% of revenue as referrals
        "W": tvl * (0.03 + max(0, rng.normal(0, 0.02))),  # 3% ± 2%
        "growth": 0.03 + rng.normal(0, 0.015),  # 3% monthly user growth
    }


def scenario_bear(month: int, tvl: float, rng: np.random.Generator) -> Dict[str, float]:
    """Sustained downturn — revenue cut in half, costs unchanged."""
    r_base = tvl * 0.010  # 1% monthly (down from 2.5%)
    return {
        "R": r_base * (1 + rng.normal(0, 0.20)),
        "C": tvl * 0.008 + 3000,
        "Ref": r_base * 0.10,
        "W": tvl * (0.06 + max(0, rng.normal(0, 0.03))),  # 6% withdrawals
        "growth": -0.01 + rng.normal(0, 0.01),  # -1% monthly
    }


def scenario_bull(month: int, tvl: float, rng: np.random.Generator) -> Dict[str, float]:
    """Bull market — strong revenue, new users flowing in."""
    r_base = tvl * 0.045  # 4.5% monthly
    return {
        "R": r_base * (1 + rng.normal(0, 0.15)),
        "C": tvl * 0.008 + 3000,
        "Ref": r_base * 0.18,       # more referrals in growth phase
        "W": tvl * (0.02 + max(0, rng.normal(0, 0.015))),  # 2% withdrawals
        "growth": 0.08 + rng.normal(0, 0.02),  # 8% monthly
    }


def scenario_crisis(month: int, tvl: float, rng: np.random.Generator) -> Dict[str, float]:
    """Black swan — month 3 bank run, slow recovery."""
    if month == 3:
        # Bank run month
        return {
            "R": tvl * 0.012,
            "C": tvl * 0.008 + 3000,
            "Ref": tvl * 0.001,
            "W": tvl * 0.40,  # 40% withdrawal!
            "growth": -0.05,
        }
    if month < 3:
        return scenario_base(month, tvl, rng)
    # Recovery months
    return {
        "R": tvl * 0.020 * (1 + rng.normal(0, 0.15)),
        "C": tvl * 0.008 + 3000,
        "Ref": tvl * 0.002,
        "W": tvl * (0.05 + max(0, rng.normal(0, 0.02))),
        "growth": 0.01 + rng.normal(0, 0.01),
    }


SCENARIOS = {
    "base": scenario_base,
    "bear": scenario_bear,
    "bull": scenario_bull,
    "crisis": scenario_crisis,
}


# ============================================================
# Simulation
# ============================================================

def run_simulation(
    scenario: str,
    initial_tvl: float,
    months: int = 12,
    initial_buffer_ratio: float = 0.30,
    k: float = 0.5,
    seed: int = 42,
) -> List[PeriodResult]:
    rng = np.random.default_rng(seed)
    scenario_fn = SCENARIOS[scenario]

    U = initial_tvl
    B = initial_tvl * initial_buffer_ratio
    L = initial_tvl * 0.30  # 30% of TVL is liquid
    current_k = k

    results: List[PeriodResult] = []

    for m in range(1, months + 1):
        params = scenario_fn(m, U, rng)

        state = PeriodState(
            month=m,
            U=U,
            B=B,
            L=L,
            R=params["R"],
            C=params["C"],
            Ref=params["Ref"],
            W=params["W"],
            k=current_k,
        )

        result = calculate_period(state)
        results.append(result)

        # Evolve state
        U = result.U_end * (1 + params["growth"])  # growth adds new deposits
        B = result.B_end
        L = max(U * 0.30, B * 0.5)  # L tracks both TVL and buffer

        # Adaptive k: if consistently healthy, nudge k up; if stressed, down
        if result.CR > 3.0 and current_k < 0.7:
            current_k = min(0.7, current_k + 0.05)
        elif result.CR < 1.2 and current_k > 0.3:
            current_k = max(0.3, current_k - 0.05)

    return results


# ============================================================
# Reporting
# ============================================================

def print_report(scenario: str, results: List[PeriodResult]):
    print(f"\n{'=' * 95}")
    print(f"SCENARIO: {scenario.upper()}")
    print(f"{'=' * 95}")
    header = f"{'M':>3} {'U_start':>11} {'R':>9} {'Net':>9} {'P':>9} {'CR':>6} {'APY':>7} {'B%':>6} {'Breakers'}"
    print(header)
    print("-" * 95)

    for r in results:
        breakers = ",".join(b[:3] for b in r.active_breakers) if r.active_breakers else "-"
        print(
            f"{r.month:>3} "
            f"{r.U_start:>11,.0f} "
            f"{r.R:>9,.0f} "
            f"{r.Net:>9,.0f} "
            f"{r.P:>9,.0f} "
            f"{r.CR:>6.2f} "
            f"{r.implied_APY*100:>6.1f}% "
            f"{r.buffer_ratio*100:>5.1f}% "
            f"{breakers}"
        )

    # Summary
    final = results[-1]
    total_distributed = sum(r.P for r in results)
    total_revenue = sum(r.R for r in results)
    total_withdrawals = sum(r.W for r in results)
    months_with_breakers = sum(1 for r in results if r.active_breakers)
    avg_cr = np.mean([r.CR for r in results if r.CR < 999])
    min_cr = min(r.CR for r in results if r.CR < 999)

    print("-" * 95)
    print(f"SUMMARY after {len(results)} months:")
    print(f"  Final TVL:           ${final.U_end:,.0f}")
    print(f"  Final Buffer:        ${final.B_end:,.0f}  ({final.B_end/max(final.U_end,1)*100:.1f}% of TVL)")
    print(f"  Total Revenue:       ${total_revenue:,.0f}")
    print(f"  Total Distributed:   ${total_distributed:,.0f}")
    print(f"  Total Withdrawals:   ${total_withdrawals:,.0f}")
    print(f"  Avg CR:              {avg_cr:.2f}")
    print(f"  Min CR:              {min_cr:.2f}")
    print(f"  Months w/ breakers:  {months_with_breakers}/{len(results)}")
    print(f"  System survival:     {'YES ✓' if min_cr >= 0.3 else 'FAILED ✗'}")


def save_csv(scenario: str, results: List[PeriodResult], output_dir: Path):
    csv_path = output_dir / f"simulation_{scenario}.csv"
    fields = list(asdict(results[0]).keys())
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            row = asdict(r)
            row["active_breakers"] = ",".join(row["active_breakers"])
            writer.writerow(row)
    print(f"CSV saved: {csv_path}")


def plot_results(scenario: str, results: List[PeriodResult], output_dir: Path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not installed — skipping chart. Install: pip install matplotlib")
        return

    months = [r.month for r in results]
    tvl = [r.U_start for r in results]
    buffer = [r.B_start for r in results]
    cr = [min(r.CR, 10) for r in results]  # clip for readability
    apy = [r.implied_APY * 100 for r in results]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle(f"SLH Dynamic Yield Simulation — {scenario.upper()}", fontsize=15, fontweight='bold')

    ax1 = axes[0, 0]
    ax1.plot(months, tvl, label="TVL (U)", color="#06b6d4", linewidth=2)
    ax1.plot(months, buffer, label="Buffer (B)", color="#ffd700", linewidth=2)
    ax1.set_title("TVL & Buffer Evolution")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("USD")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2 = axes[0, 1]
    ax2.plot(months, cr, color="#a855f7", linewidth=2)
    ax2.axhline(y=1.0, color="red", linestyle="--", label="CR=1.0 (danger)")
    ax2.axhline(y=1.5, color="orange", linestyle="--", label="CR=1.5 (target)")
    ax2.set_title("Coverage Ratio over time")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("CR")
    ax2.legend()
    ax2.grid(alpha=0.3)

    ax3 = axes[1, 0]
    ax3.plot(months, apy, color="#00e887", linewidth=2)
    ax3.set_title("Implied APY (not a promise)")
    ax3.set_xlabel("Month")
    ax3.set_ylabel("%")
    ax3.grid(alpha=0.3)

    ax4 = axes[1, 1]
    breaker_count = [len(r.active_breakers) for r in results]
    colors = ["#00e887" if c == 0 else "#ffc107" if c == 1 else "#ff9800" if c == 2 else "#ff4444" for c in breaker_count]
    ax4.bar(months, breaker_count, color=colors)
    ax4.set_title("Active Circuit Breakers per month")
    ax4.set_xlabel("Month")
    ax4.set_ylabel("# breakers")
    ax4.set_ylim(0, 4)
    ax4.grid(alpha=0.3, axis="y")

    plt.tight_layout()
    chart_path = output_dir / f"simulation_{scenario}.png"
    plt.savefig(chart_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"Chart saved: {chart_path}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="SLH Dynamic Yield Treasury Simulation")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()) + ["all"],
                        default="base", help="Scenario to simulate")
    parser.add_argument("--tvl", type=float, default=500000, help="Initial TVL")
    parser.add_argument("--months", type=int, default=12, help="Months to simulate")
    parser.add_argument("--buffer-ratio", type=float, default=0.30, help="Starting buffer/TVL ratio")
    parser.add_argument("--k", type=float, default=0.5, help="Distribution coefficient")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--output", default="./simulation_output",
                        help="Output directory for CSV/charts")
    parser.add_argument("--no-plot", action="store_true", help="Skip matplotlib charts")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios_to_run = SCENARIOS.keys() if args.scenario == "all" else [args.scenario]

    for scenario in scenarios_to_run:
        results = run_simulation(
            scenario=scenario,
            initial_tvl=args.tvl,
            months=args.months,
            initial_buffer_ratio=args.buffer_ratio,
            k=args.k,
            seed=args.seed,
        )
        print_report(scenario, results)
        save_csv(scenario, results, output_dir)
        if not args.no_plot:
            plot_results(scenario, results, output_dir)

    print(f"\nAll output in: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
