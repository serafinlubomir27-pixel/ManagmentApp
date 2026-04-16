"""
CPM Manager — bridge between the pure CPM engine and the database repositories.
Fetches tasks + dependencies, runs CPM, saves results back.
"""
from __future__ import annotations

from logic.cpm_engine import CPMTask, CPMResult, calculate_cpm, calculate_health_score
from repositories import task_repo


def recalculate_project_cpm(project_id: int) -> CPMResult:
    """
    1. Fetch all tasks for project
    2. Fetch all dependencies
    3. Build CPMTask list
    4. Run calculate_cpm()
    5. Save CPM results back to DB
    6. Return CPMResult
    """
    # Fetch tasks
    task_rows = task_repo.get_tasks_for_project_with_cpm(project_id)
    if not task_rows:
        return CPMResult(
            tasks=[], critical_path=[], project_duration=0,
            project_duration_without_delays=0, total_project_delay=0,
            is_valid=True, errors=[],
        )

    # Fetch dependencies
    dep_rows = task_repo.get_all_dependencies_for_project(project_id)

    # Build dependency map: task_id -> [depends_on_task_id, ...]
    dep_map: dict[int, list[int]] = {}
    for d in dep_rows:
        tid = d["task_id"]
        dep_map.setdefault(tid, []).append(d["depends_on_task_id"])

    # Build CPMTask list
    cpm_tasks = [
        CPMTask(
            id=row["id"],
            name=row["name"],
            duration=row.get("duration") or 1,
            dependencies=dep_map.get(row["id"], []),
            delay_days=row.get("delay_days") or 0,
            status=row.get("status", "pending"),
        )
        for row in task_rows
    ]

    # Run CPM
    result = calculate_cpm(cpm_tasks)

    # Save results back to DB
    if result.is_valid:
        for t in result.tasks:
            task_repo.update_task_cpm_fields(
                task_id=t.id,
                es=t.es,
                ef=t.ef,
                ls=t.ls,
                lf=t.lf,
                total_float=t.total_float,
                is_critical=t.is_critical,
            )

    return result


def get_project_health(project_id: int, planned_end_days: int = 30) -> tuple[int, str]:
    """
    Run CPM and return (health_score, label).
    """
    result = recalculate_project_cpm(project_id)
    if not result.tasks:
        return 100, "Healthy"

    return calculate_health_score(
        tasks=result.tasks,
        project_duration=result.project_duration,
        planned_end_days=planned_end_days,
    )
