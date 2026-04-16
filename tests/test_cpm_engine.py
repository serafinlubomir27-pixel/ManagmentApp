"""Unit tests for logic/cpm_engine.py

Run with:
    py -m pytest tests/test_cpm_engine.py -v
"""
import pytest
from datetime import date
from logic.cpm_engine import (
    CPMTask,
    CPMResult,
    calculate_cpm,
    calculate_health_score,
    detect_cycle,
    topological_sort,
    forward_pass,
    backward_pass,
    would_create_cycle,
    calculate_dates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(id_, name, duration, deps=None, delay=0, status="pending"):
    return CPMTask(
        id=id_, name=name, duration=duration,
        dependencies=deps or [], delay_days=delay, status=status,
    )


def task_map(tasks):
    return {t.id: t for t in tasks}


# ---------------------------------------------------------------------------
# detect_cycle
# ---------------------------------------------------------------------------

class TestDetectCycle:
    def test_no_cycle_linear(self):
        tasks = [make_task(1, "A", 3), make_task(2, "B", 2, [1])]
        assert detect_cycle(tasks) is None

    def test_no_cycle_diamond(self):
        tasks = [
            make_task(1, "A", 3),
            make_task(2, "B", 2, [1]),
            make_task(3, "C", 1, [1]),
            make_task(4, "D", 4, [2, 3]),
        ]
        assert detect_cycle(tasks) is None

    def test_simple_cycle(self):
        # 1 → 2 → 1 (mutual dependency)
        tasks = [make_task(1, "A", 3, [2]), make_task(2, "B", 2, [1])]
        result = detect_cycle(tasks)
        assert result is not None
        assert len(result) >= 2

    def test_self_loop(self):
        tasks = [make_task(1, "A", 3, [1])]
        result = detect_cycle(tasks)
        assert result is not None

    def test_longer_cycle(self):
        # 1 → 2 → 3 → 1
        tasks = [
            make_task(1, "A", 3, [3]),
            make_task(2, "B", 2, [1]),
            make_task(3, "C", 1, [2]),
        ]
        result = detect_cycle(tasks)
        assert result is not None

    def test_empty(self):
        assert detect_cycle([]) is None

    def test_single_task_no_deps(self):
        assert detect_cycle([make_task(1, "A", 5)]) is None

    def test_dependency_outside_task_set(self):
        # Task depends on id=99 which doesn't exist — should be ignored, not crash
        tasks = [make_task(1, "A", 3, [99])]
        assert detect_cycle(tasks) is None


# ---------------------------------------------------------------------------
# topological_sort
# ---------------------------------------------------------------------------

class TestTopologicalSort:
    def test_linear_order(self):
        tasks = [make_task(2, "B", 2, [1]), make_task(1, "A", 3)]
        result = topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index(1) < ids.index(2)

    def test_diamond(self):
        tasks = [
            make_task(4, "D", 4, [2, 3]),
            make_task(2, "B", 2, [1]),
            make_task(3, "C", 1, [1]),
            make_task(1, "A", 3),
        ]
        result = topological_sort(tasks)
        ids = [t.id for t in result]
        assert ids.index(1) < ids.index(2)
        assert ids.index(1) < ids.index(3)
        assert ids.index(2) < ids.index(4)
        assert ids.index(3) < ids.index(4)

    def test_no_deps_all_returned(self):
        tasks = [make_task(i, f"T{i}", 1) for i in range(1, 6)]
        result = topological_sort(tasks)
        assert len(result) == 5


# ---------------------------------------------------------------------------
# forward_pass / backward_pass
# ---------------------------------------------------------------------------

class TestForwardPass:
    def test_single_task(self):
        tasks = [make_task(1, "A", 5)]
        forward_pass(tasks)
        assert tasks[0].es == 0
        assert tasks[0].ef == 5

    def test_linear_chain(self):
        tasks = topological_sort([
            make_task(1, "A", 3),
            make_task(2, "B", 4, [1]),
            make_task(3, "C", 2, [2]),
        ])
        forward_pass(tasks)
        tm = task_map(tasks)
        assert tm[1].es == 0 and tm[1].ef == 3
        assert tm[2].es == 3 and tm[2].ef == 7
        assert tm[3].es == 7 and tm[3].ef == 9

    def test_delay_days(self):
        tasks = topological_sort([
            make_task(1, "A", 3),
            make_task(2, "B", 2, [1], delay=1),
        ])
        forward_pass(tasks)
        tm = task_map(tasks)
        # B starts after A finishes (3) + delay (1) = 4
        assert tm[2].es == 4
        assert tm[2].ef == 6

    def test_parallel_then_merge(self):
        tasks = topological_sort([
            make_task(1, "A", 2),
            make_task(2, "B", 5, [1]),
            make_task(3, "C", 3, [1]),
            make_task(4, "D", 1, [2, 3]),
        ])
        forward_pass(tasks)
        tm = task_map(tasks)
        # D waits for the longer path: A(2)+B(5)=7, A(2)+C(3)=5 → D.es=7
        assert tm[4].es == 7
        assert tm[4].ef == 8


class TestBackwardPass:
    def test_linear_chain(self):
        tasks = topological_sort([
            make_task(1, "A", 3),
            make_task(2, "B", 4, [1]),
            make_task(3, "C", 2, [2]),
        ])
        forward_pass(tasks)
        project_duration = max(t.ef for t in tasks)
        backward_pass(tasks, project_duration)
        tm = task_map(tasks)
        # C is the last — LF=9, LS=7
        assert tm[3].lf == 9 and tm[3].ls == 7
        # B: LF = LS of C = 7, LS = 7-4 = 3
        assert tm[2].lf == 7 and tm[2].ls == 3
        # A: LF = LS of B = 3, LS = 3-3 = 0
        assert tm[1].lf == 3 and tm[1].ls == 0


# ---------------------------------------------------------------------------
# calculate_cpm — full integration
# ---------------------------------------------------------------------------

class TestCalculateCPM:
    def test_empty_input(self):
        result = calculate_cpm([])
        assert result.is_valid
        assert result.project_duration == 0
        assert result.critical_path == []

    def test_single_task(self):
        result = calculate_cpm([make_task(1, "A", 5)])
        assert result.is_valid
        assert result.project_duration == 5
        assert 1 in result.critical_path

    def test_linear_chain_critical_path(self):
        tasks = [
            make_task(1, "A", 3),
            make_task(2, "B", 4, [1]),
            make_task(3, "C", 2, [2]),
        ]
        result = calculate_cpm(tasks)
        assert result.is_valid
        assert result.project_duration == 9
        # All tasks on critical path (linear chain, zero float everywhere)
        assert set(result.critical_path) == {1, 2, 3}

    def test_parallel_paths_critical_is_longer(self):
        # A → B (duration 5) and A → C (duration 2), both → D
        tasks = [
            make_task(1, "A", 2),
            make_task(2, "B", 5, [1]),   # longer path: 2+5=7
            make_task(3, "C", 2, [1]),   # shorter: 2+2=4
            make_task(4, "D", 1, [2, 3]),
        ]
        result = calculate_cpm(tasks)
        assert result.is_valid
        assert result.project_duration == 8  # A(2)+B(5)+D(1)
        # Critical path: A, B, D (not C — C has float)
        assert 1 in result.critical_path
        assert 2 in result.critical_path
        assert 4 in result.critical_path
        assert 3 not in result.critical_path

    def test_cycle_detected(self):
        tasks = [make_task(1, "A", 3, [2]), make_task(2, "B", 2, [1])]
        result = calculate_cpm(tasks)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_float_calculation(self):
        tasks = [
            make_task(1, "A", 2),
            make_task(2, "B", 5, [1]),
            make_task(3, "C", 2, [1]),
            make_task(4, "D", 1, [2, 3]),
        ]
        result = calculate_cpm(tasks)
        tm = task_map(result.tasks)
        # C has float: project=8, C.ef=6, D.ls=7 → C.lf=7, C.ls=5, C.float=5-4=1...
        # Actually: C.es=2, C.ef=4, C.ls=5, C.lf=7 → float=3
        assert tm[3].total_float > 0
        # B has zero float (critical)
        assert tm[2].total_float == 0

    def test_delay_increases_project_duration(self):
        tasks_no_delay = [make_task(1, "A", 3), make_task(2, "B", 4, [1])]
        tasks_with_delay = [make_task(1, "A", 3), make_task(2, "B", 4, [1], delay=2)]
        r1 = calculate_cpm(tasks_no_delay)
        r2 = calculate_cpm(tasks_with_delay)
        assert r2.project_duration == r1.project_duration + 2
        assert r2.total_project_delay == 2

    def test_all_tasks_in_result(self):
        tasks = [make_task(i, f"T{i}", i) for i in range(1, 6)]
        result = calculate_cpm(tasks)
        assert len(result.tasks) == 5


# ---------------------------------------------------------------------------
# calculate_health_score
# ---------------------------------------------------------------------------

class TestCalculateHealthScore:
    def _make_result_tasks(self):
        tasks = [
            make_task(1, "A", 3, status="completed"),
            make_task(2, "B", 4, [1], status="in_progress"),
        ]
        result = calculate_cpm(tasks)
        return result.tasks

    def test_perfect_project(self):
        tasks = [make_task(1, "A", 3, status="completed")]
        result = calculate_cpm(tasks)
        score, label = calculate_health_score(result.tasks, result.project_duration, 10)
        assert score == 100
        assert label == "Healthy"

    def test_score_decreases_with_slippage(self):
        tasks = [make_task(1, "A", 10)]
        result = calculate_cpm(tasks)
        score, _ = calculate_health_score(result.tasks, result.project_duration, 5)
        # slippage = 10-5=5, penalty = 5*2=10
        assert score == 90

    def test_score_decreases_with_delays(self):
        tasks = [make_task(1, "A", 3, delay=5)]
        result = calculate_cpm(tasks)
        score_no_delay, _ = calculate_health_score(result.tasks, 8, 20)
        tasks2 = [make_task(1, "A", 3)]
        result2 = calculate_cpm(tasks2)
        score_with_delay, _ = calculate_health_score(result2.tasks, 3, 20)
        assert score_no_delay < score_with_delay

    def test_label_at_risk(self):
        tasks = [make_task(1, "A", 50)]
        result = calculate_cpm(tasks)
        score, label = calculate_health_score(result.tasks, result.project_duration, 10)
        assert label in ("At Risk", "Critical")

    def test_score_never_negative(self):
        tasks = [make_task(1, "A", 100, delay=50)]
        result = calculate_cpm(tasks)
        score, _ = calculate_health_score(result.tasks, result.project_duration, 1)
        assert score >= 0


# ---------------------------------------------------------------------------
# would_create_cycle
# ---------------------------------------------------------------------------

class TestWouldCreateCycle:
    def test_safe_dependency(self):
        tasks = [make_task(1, "A", 3), make_task(2, "B", 2, [1])]
        # Adding 2→3 (new task 3 depends on 2) is fine
        tasks.append(make_task(3, "C", 1))
        assert not would_create_cycle(tasks, from_task_id=2, to_task_id=3)

    def test_creates_cycle(self):
        tasks = [make_task(1, "A", 3), make_task(2, "B", 2, [1])]
        # Adding B→A would create cycle
        assert would_create_cycle(tasks, from_task_id=2, to_task_id=1)

    def test_longer_chain_creates_cycle(self):
        tasks = [
            make_task(1, "A", 3),
            make_task(2, "B", 2, [1]),
            make_task(3, "C", 1, [2]),
        ]
        # Adding C→A (3→1) would create cycle: A→B→C→A
        assert would_create_cycle(tasks, from_task_id=3, to_task_id=1)


# ---------------------------------------------------------------------------
# calculate_dates
# ---------------------------------------------------------------------------

class TestCalculateDates:
    def test_single_task_dates(self):
        tasks = [make_task(1, "A", 5)]
        result = calculate_cpm(tasks)
        start = date(2026, 1, 1)
        dates = calculate_dates(result.tasks, start)
        assert dates[1][0] == date(2026, 1, 1)   # ES=0 → start
        assert dates[1][1] == date(2026, 1, 6)   # EF=5 → start + 5 days

    def test_chain_dates(self):
        tasks = [make_task(1, "A", 3), make_task(2, "B", 4, [1])]
        result = calculate_cpm(tasks)
        start = date(2026, 1, 1)
        dates = calculate_dates(result.tasks, start)
        assert dates[2][0] == date(2026, 1, 4)   # B starts after A: day 3 → Jan 4
        assert dates[2][1] == date(2026, 1, 8)   # B ends: day 7 → Jan 8
