"""PERT (Program Evaluation and Review Technique) engine.

Extends CPM with probabilistic task duration estimates:
  a = optimistic, m = most likely (= CPM duration), b = pessimistic

PERT formulas:
  E  = (a + 4m + b) / 6          — expected duration
  σ  = (b - a) / 6               — standard deviation
  V  = σ²                        — variance

Project-level:
  E_project  = sum of E on critical path
  V_project  = sum of V on critical path
  σ_project  = sqrt(V_project)
  P(T ≤ D)   = Φ((D - E_project) / σ_project)  — probability of meeting deadline D
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import NormalDist

from logic.cpm_engine import CPMTask, CPMResult, calculate_cpm


@dataclass
class PERTTask:
    """Holds PERT-specific fields for one task."""
    task_id: int
    name: str
    duration_optimistic: float    # a
    duration_likely: float        # m (same as CPM duration)
    duration_pessimistic: float   # b
    pert_expected: float          # E = (a + 4m + b) / 6
    pert_std_dev: float           # σ = (b - a) / 6
    pert_variance: float          # V = σ²
    is_critical: bool = False


@dataclass
class PERTResult:
    pert_tasks: list[PERTTask]
    critical_path_ids: list[int]
    project_expected_duration: float      # E_project
    project_std_dev: float                # σ_project
    project_variance: float               # V_project
    probability_by_deadline: dict[int, float]  # deadline_days -> probability (0-1)
    cpm_result: CPMResult


def calculate_pert(
    cpm_tasks: list[CPMTask],
    task_pert_data: dict[int, tuple[float, float, float]],  # task_id -> (a, m, b)
    deadline_days: int | None = None,
) -> PERTResult:
    """
    Calculate PERT analysis.

    Args:
        cpm_tasks: List of CPMTask objects (with standard duration = m)
        task_pert_data: Dict mapping task_id to (optimistic, likely, pessimistic)
                        Tasks not in this dict use duration as all three estimates.
        deadline_days: Optional project deadline for probability calculation

    Returns:
        PERTResult with full analysis
    """
    # Build PERT tasks
    pert_tasks: list[PERTTask] = []

    # Run standard CPM first to get critical path
    cpm_result = calculate_cpm(cpm_tasks)
    critical_ids = set(cpm_result.critical_path)

    for t in cpm_tasks:
        if t.id in task_pert_data:
            a, m, b = task_pert_data[t.id]
        else:
            a = m = b = float(t.duration)

        E = (a + 4 * m + b) / 6
        sigma = (b - a) / 6
        V = sigma ** 2

        pert_tasks.append(PERTTask(
            task_id=t.id,
            name=t.name,
            duration_optimistic=a,
            duration_likely=m,
            duration_pessimistic=b,
            pert_expected=round(E, 2),
            pert_std_dev=round(sigma, 2),
            pert_variance=round(V, 4),
            is_critical=t.id in critical_ids,
        ))

    # Project-level stats (only critical path tasks)
    critical_pert = [pt for pt in pert_tasks if pt.is_critical]
    E_project = sum(pt.pert_expected for pt in critical_pert)
    V_project = sum(pt.pert_variance for pt in critical_pert)
    sigma_project = math.sqrt(V_project) if V_project > 0 else 0.0

    # Probability calculations for multiple deadlines
    prob_by_deadline: dict[int, float] = {}

    # Always calculate for ±30% range around expected
    deadlines_to_calc = []
    if deadline_days is not None:
        deadlines_to_calc.append(deadline_days)

    # Add standard checkpoints relative to expected duration
    base = round(E_project)
    for offset in [-5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10]:
        d = base + offset
        if d > 0:
            deadlines_to_calc.append(d)

    dist = NormalDist(mu=E_project, sigma=sigma_project) if sigma_project > 0 else None

    for d in set(deadlines_to_calc):
        if sigma_project == 0:
            prob = 1.0 if d >= E_project else 0.0
        else:
            prob = dist.cdf(d)
        prob_by_deadline[d] = round(prob, 4)

    return PERTResult(
        pert_tasks=pert_tasks,
        critical_path_ids=list(critical_ids),
        project_expected_duration=round(E_project, 2),
        project_std_dev=round(sigma_project, 2),
        project_variance=round(V_project, 4),
        probability_by_deadline=prob_by_deadline,
        cpm_result=cpm_result,
    )
