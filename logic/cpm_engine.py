"""Pure CPM (Critical Path Method) engine. No database, no UI — just algorithm."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CPMTask:
    id: int
    name: str
    duration: int
    dependencies: list[int] = field(default_factory=list)  # IDs this task depends on
    delay_days: int = 0
    status: str = "pending"
    es: int = 0   # Earliest Start
    ef: int = 0   # Earliest Finish
    ls: int = 0   # Latest Start
    lf: int = 0   # Latest Finish
    total_float: int = 0
    is_critical: bool = False


@dataclass
class CPMResult:
    tasks: list[CPMTask]
    critical_path: list[int]          # task IDs on critical path
    project_duration: int
    project_duration_without_delays: int
    total_project_delay: int
    is_valid: bool
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cycle detection (DFS)
# ---------------------------------------------------------------------------

def detect_cycle(tasks: list[CPMTask]) -> list[int] | None:
    """Return a list of task IDs forming a cycle, or None if acyclic."""
    task_map: dict[int, CPMTask] = {t.id: t for t in tasks}
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[int, int] = {t.id: WHITE for t in tasks}
    parent: dict[int, int | None] = {t.id: None for t in tasks}

    def dfs(uid: int) -> list[int] | None:
        color[uid] = GRAY
        for dep_id in task_map[uid].dependencies:
            if dep_id not in color:
                continue  # dependency points outside this task set — skip
            if color[dep_id] == GRAY:
                # back-edge found — reconstruct cycle
                cycle = [dep_id, uid]
                cur = uid
                while cur != dep_id:
                    cur = parent[cur]  # type: ignore[assignment]
                    if cur is None:
                        break
                    cycle.append(cur)
                cycle.reverse()
                return cycle
            if color[dep_id] == WHITE:
                parent[dep_id] = uid
                result = dfs(dep_id)
                if result is not None:
                    return result
        color[uid] = BLACK
        return None

    for t in tasks:
        if color[t.id] == WHITE:
            result = dfs(t.id)
            if result is not None:
                return result
    return None


# ---------------------------------------------------------------------------
# Topological sort (Kahn's algorithm)
# ---------------------------------------------------------------------------

def topological_sort(tasks: list[CPMTask]) -> list[CPMTask]:
    """Return tasks in dependency order using Kahn's algorithm."""
    task_map: dict[int, CPMTask] = {t.id: t for t in tasks}
    valid_ids = set(task_map.keys())
    in_degree: dict[int, int] = {t.id: 0 for t in tasks}

    for t in tasks:
        for dep_id in t.dependencies:
            if dep_id in valid_ids:
                in_degree[t.id] += 1

    queue: list[int] = [tid for tid, deg in in_degree.items() if deg == 0]
    result: list[CPMTask] = []

    while queue:
        uid = queue.pop(0)
        result.append(task_map[uid])
        # find tasks that depend on uid
        for t in tasks:
            if uid in t.dependencies and t.id in valid_ids:
                in_degree[t.id] -= 1
                if in_degree[t.id] == 0:
                    queue.append(t.id)

    return result


# ---------------------------------------------------------------------------
# Forward pass
# ---------------------------------------------------------------------------

def forward_pass(tasks: list[CPMTask]) -> None:
    """Calculate ES and EF for each task (in topological order). Mutates tasks."""
    task_map: dict[int, CPMTask] = {t.id: t for t in tasks}

    for t in tasks:
        valid_deps = [d for d in t.dependencies if d in task_map]
        if not valid_deps:
            t.es = 0 + t.delay_days
        else:
            t.es = max(task_map[d].ef for d in valid_deps) + t.delay_days
        t.ef = t.es + t.duration


# ---------------------------------------------------------------------------
# Backward pass
# ---------------------------------------------------------------------------

def backward_pass(tasks: list[CPMTask], project_duration: int) -> None:
    """Calculate LS and LF for each task (reverse topological order). Mutates tasks."""
    task_map: dict[int, CPMTask] = {t.id: t for t in tasks}
    valid_ids = set(task_map.keys())

    # Build dependents map (reverse of dependencies)
    dependents: dict[int, list[int]] = {t.id: [] for t in tasks}
    for t in tasks:
        for dep_id in t.dependencies:
            if dep_id in valid_ids:
                dependents[dep_id].append(t.id)

    for t in reversed(tasks):
        if not dependents[t.id]:
            # end task
            t.lf = project_duration
        else:
            t.lf = min(task_map[d].ls for d in dependents[t.id])
        t.ls = t.lf - t.duration


# ---------------------------------------------------------------------------
# Main CPM calculation
# ---------------------------------------------------------------------------

def calculate_cpm(tasks: list[CPMTask]) -> CPMResult:
    """Orchestrate the full CPM calculation and return a CPMResult."""
    if not tasks:
        return CPMResult(
            tasks=[],
            critical_path=[],
            project_duration=0,
            project_duration_without_delays=0,
            total_project_delay=0,
            is_valid=True,
            errors=[],
        )

    # 1. Cycle detection
    cycle = detect_cycle(tasks)
    if cycle is not None:
        return CPMResult(
            tasks=tasks,
            critical_path=[],
            project_duration=0,
            project_duration_without_delays=0,
            total_project_delay=0,
            is_valid=False,
            errors=[f"Cycle detected among tasks: {cycle}"],
        )

    # 2. Topological sort
    sorted_tasks = topological_sort(tasks)

    # 3. Forward pass
    forward_pass(sorted_tasks)
    project_duration = max(t.ef for t in sorted_tasks) if sorted_tasks else 0

    # 4. Backward pass
    backward_pass(sorted_tasks, project_duration)

    # 5. Float & criticality
    for t in sorted_tasks:
        t.total_float = t.ls - t.es
        t.is_critical = t.total_float == 0

    # 6. Critical path (sorted by ES)
    critical_path = sorted(
        [t.id for t in sorted_tasks if t.is_critical],
        key=lambda tid: next(t.es for t in sorted_tasks if t.id == tid),
    )

    # 7. Baseline (without delays)
    baseline_tasks = [
        CPMTask(
            id=t.id,
            name=t.name,
            duration=t.duration,
            dependencies=list(t.dependencies),
            delay_days=0,
            status=t.status,
        )
        for t in sorted_tasks
    ]
    baseline_sorted = topological_sort(baseline_tasks)
    forward_pass(baseline_sorted)
    project_duration_without_delays = max(t.ef for t in baseline_sorted) if baseline_sorted else 0

    # 8. Total delay
    total_project_delay = project_duration - project_duration_without_delays

    return CPMResult(
        tasks=sorted_tasks,
        critical_path=critical_path,
        project_duration=project_duration,
        project_duration_without_delays=project_duration_without_delays,
        total_project_delay=total_project_delay,
        is_valid=True,
        errors=[],
    )


# ---------------------------------------------------------------------------
# Health score
# ---------------------------------------------------------------------------

def calculate_health_score(
    tasks: list[CPMTask],
    project_duration: int,
    planned_end_days: int,
) -> tuple[int, str]:
    """Return (score 0-100, label) based on project health heuristics."""
    score = 100

    blocked_count = sum(1 for t in tasks if t.status == "pending" and t.dependencies)
    score -= blocked_count * 10

    overdue_critical_count = sum(
        1 for t in tasks if t.is_critical and t.status != "completed" and t.ef > t.lf
    )
    score -= overdue_critical_count * 15

    slippage = max(0, project_duration - planned_end_days)
    score -= slippage * 2

    total_delay = sum(t.delay_days for t in tasks)
    score -= total_delay * 3

    score = max(0, score)

    if score >= 80:
        label = "Healthy"
    elif score >= 60:
        label = "At Risk"
    else:
        label = "Critical"

    return score, label


# ---------------------------------------------------------------------------
# Utility: would adding a dependency create a cycle?
# ---------------------------------------------------------------------------

def would_create_cycle(
    tasks: list[CPMTask], from_task_id: int, to_task_id: int
) -> bool:
    """Check if adding dependency from_task → to_task would create a cycle."""
    test_tasks = [
        CPMTask(
            id=t.id, name=t.name, duration=t.duration,
            dependencies=(
                t.dependencies + [from_task_id]
                if t.id == to_task_id
                else list(t.dependencies)
            ),
            delay_days=t.delay_days, status=t.status,
        )
        for t in tasks
    ]
    return detect_cycle(test_tasks) is not None


# ---------------------------------------------------------------------------
# Utility: calculate real dates from CPM + project start
# ---------------------------------------------------------------------------

def calculate_dates(
    tasks: list[CPMTask], project_start: date
) -> dict[int, tuple[date, date]]:
    """Return {task_id: (start_date, end_date)} based on ES/EF + project start."""
    return {
        t.id: (
            project_start + timedelta(days=t.es),
            project_start + timedelta(days=t.ef),
        )
        for t in tasks
    }
