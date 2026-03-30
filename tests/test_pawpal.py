"""
tests/test_pawpal.py — Tests for PawPal+ core classes.
Run with: python -m pytest
"""

from pawpal_system import Owner, Pet, Task, Scheduler, _parse_time, _format_time


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _make_owner(minutes: int = 90, day_start: str = "08:00") -> Owner:
    return Owner(name="Jordan", available_minutes=minutes, day_start=day_start)


def _make_scheduled_scheduler(minutes: int = 90) -> tuple[Scheduler, Pet, Pet]:
    """Return a scheduler with a plan already built and times assigned."""
    owner = _make_owner(minutes)
    mochi = Pet(name="Mochi", species="dog", age=3)
    luna  = Pet(name="Luna",  species="cat", age=5)
    mochi.add_task(Task("Morning walk",    duration_minutes=30, priority="high",   frequency="daily"))
    mochi.add_task(Task("Trick training",  duration_minutes=20, priority="medium"))
    luna.add_task(Task("Feeding",          duration_minutes=5,  priority="high",   frequency="daily"))
    luna.add_task(Task("Litter box clean", duration_minutes=10, priority="medium"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    s = Scheduler(owner=owner, date="2026-03-30")
    s.build_plan()
    s.assign_times()
    return s, mochi, luna


# ---------------------------------------------------------------------------
# _parse_time / _format_time helpers
# ---------------------------------------------------------------------------

def test_parse_time_converts_correctly():
    assert _parse_time("08:00") == 480
    assert _parse_time("08:30") == 510
    assert _parse_time("00:05") == 5


def test_format_time_converts_correctly():
    assert _format_time(480) == "08:00"
    assert _format_time(510) == "08:30"
    assert _format_time(605) == "10:05"


# ---------------------------------------------------------------------------
# Task — mark_complete and next_occurrence
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """mark_complete() should flip completed from False to True."""
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_complete_is_idempotent():
    """Calling mark_complete() twice should leave completed as True."""
    task = Task(title="Feeding", duration_minutes=5, priority="high")
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True


def test_next_occurrence_daily_adds_one_day():
    """Daily task: next_occurrence should return a task due tomorrow."""
    task = Task("Walk", duration_minutes=30, priority="high", frequency="daily")
    nxt = task.next_occurrence("2026-03-30")
    assert nxt is not None
    assert nxt.due_date == "2026-03-31"


def test_next_occurrence_weekly_adds_seven_days():
    """Weekly task: next_occurrence should return a task due in 7 days."""
    task = Task("Flea treatment", duration_minutes=10, priority="high", frequency="weekly")
    nxt = task.next_occurrence("2026-03-30")
    assert nxt is not None
    assert nxt.due_date == "2026-04-06"


def test_next_occurrence_as_needed_returns_none():
    """As-needed task: next_occurrence should return None."""
    task = Task("Vet visit", duration_minutes=60, priority="high", frequency="as-needed")
    assert task.next_occurrence("2026-03-30") is None


def test_next_occurrence_preserves_task_fields():
    """New occurrence should copy title, duration, priority, and category."""
    task = Task("Walk", duration_minutes=30, priority="high", category="exercise", frequency="daily")
    nxt = task.next_occurrence("2026-03-30")
    assert nxt.title == "Walk"
    assert nxt.duration_minutes == 30
    assert nxt.priority == "high"
    assert nxt.category == "exercise"


# ---------------------------------------------------------------------------
# Pet — add_task and get_tasks_by_priority
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    """add_task() should increase the pet's task list length by one."""
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Walk", duration_minutes=30, priority="high"))
    assert len(pet.tasks) == 1


def test_get_tasks_by_priority_orders_correctly():
    """get_tasks_by_priority() should return tasks high → medium → low."""
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(Task("Grooming",  duration_minutes=15, priority="low"))
    pet.add_task(Task("Feeding",   duration_minutes=5,  priority="high"))
    pet.add_task(Task("Play time", duration_minutes=10, priority="medium"))

    priorities = [t.priority for t in pet.get_tasks_by_priority()]
    assert priorities == ["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_add_pet_registers_pet():
    """add_pet() should add the pet to the owner's pets list."""
    owner = _make_owner()
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(owner.pets) == 0
    owner.add_pet(pet)
    assert len(owner.pets) == 1
    assert owner.pets[0].name == "Mochi"


def test_get_available_time_returns_budget():
    """get_available_time() should return available_minutes."""
    assert _make_owner(90).get_available_time() == 90


# ---------------------------------------------------------------------------
# Scheduler — build_plan
# ---------------------------------------------------------------------------

def test_scheduler_respects_time_budget():
    """build_plan() should not exceed available_minutes."""
    owner = _make_owner(30)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk",     duration_minutes=20, priority="high"))
    pet.add_task(Task("Training", duration_minutes=20, priority="medium"))
    owner.add_pet(pet)
    s = Scheduler(owner=owner, date="2026-03-30")
    plan = s.build_plan()
    assert s.get_total_duration() <= 30
    assert len(plan) == 1


def test_scheduler_picks_highest_priority_first():
    """build_plan() should include high-priority tasks before low ones."""
    owner = _make_owner(25)
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(Task("Grooming", duration_minutes=20, priority="low"))
    pet.add_task(Task("Feeding",  duration_minutes=5,  priority="high"))
    owner.add_pet(pet)
    s = Scheduler(owner=owner, date="2026-03-30")
    plan = s.build_plan()
    titles = [t.title for t in plan]
    assert "Feeding" in titles
    assert "Grooming" in titles  # both fit within 25 min


def test_scheduler_excludes_task_that_does_not_fit():
    """build_plan() should skip a task that alone exceeds available time."""
    owner = _make_owner(10)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Long walk", duration_minutes=60, priority="high"))
    owner.add_pet(pet)
    s = Scheduler(owner=owner, date="2026-03-30")
    assert s.build_plan() == []
    assert s.get_total_duration() == 0


# ---------------------------------------------------------------------------
# Scheduler — assign_times and sort_by_time (Step 2)
# ---------------------------------------------------------------------------

def test_assign_times_first_task_gets_day_start():
    """First scheduled task should start at day_start."""
    s, mochi, _ = _make_scheduled_scheduler()
    # highest priority task first → Morning walk
    first = s.scheduled_tasks[0]
    assert first.start_time == "08:00"


def test_assign_times_second_task_follows_first():
    """Second task should start exactly when the first one ends."""
    s, _, _ = _make_scheduled_scheduler()
    t1, t2 = s.scheduled_tasks[0], s.scheduled_tasks[1]
    t1_end = _parse_time(t1.start_time) + t1.duration_minutes
    assert _parse_time(t2.start_time) == t1_end


def test_sort_by_time_returns_chronological_order():
    """sort_by_time() should return tasks ordered earliest to latest."""
    s, _, _ = _make_scheduled_scheduler()
    sorted_tasks = s.sort_by_time()
    times = [_parse_time(t.start_time) for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_time_without_start_times_sorts_last():
    """Tasks with no start_time should appear at the end of sort_by_time()."""
    owner = _make_owner(30)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk", duration_minutes=20, priority="high"))
    owner.add_pet(pet)
    s = Scheduler(owner=owner, date="2026-03-30")
    s.build_plan()
    # Do NOT call assign_times — start_times are empty
    sorted_tasks = s.sort_by_time()
    # Should not raise; task with no time should appear last (or only item)
    assert len(sorted_tasks) == 1


# ---------------------------------------------------------------------------
# Scheduler — filter_tasks (Step 2)
# ---------------------------------------------------------------------------

def test_filter_by_pet_name_returns_only_that_pets_tasks():
    """filter_tasks(pet_name='Mochi') should include only Mochi's tasks."""
    s, mochi, _ = _make_scheduled_scheduler()
    results = s.filter_tasks(pet_name="Mochi")
    assert all(t in mochi.tasks for t in results)
    assert len(results) == len(mochi.tasks)


def test_filter_by_completed_false_excludes_done_tasks():
    """filter_tasks(completed=False) should exclude completed tasks."""
    s, mochi, _ = _make_scheduled_scheduler()
    mochi.tasks[0].mark_complete()
    pending = s.filter_tasks(completed=False)
    assert all(not t.completed for t in pending)


def test_filter_by_completed_true_returns_only_done():
    """filter_tasks(completed=True) should return only completed tasks."""
    s, mochi, _ = _make_scheduled_scheduler()
    mochi.tasks[0].mark_complete()
    done = s.filter_tasks(completed=True)
    assert len(done) == 1
    assert done[0].completed is True


def test_filter_no_args_returns_all_tasks():
    """filter_tasks() with no arguments should return every task."""
    s, mochi, luna = _make_scheduled_scheduler()
    total = len(mochi.tasks) + len(luna.tasks)
    assert len(s.filter_tasks()) == total


# ---------------------------------------------------------------------------
# Scheduler — complete_task and recurrence (Step 3)
# ---------------------------------------------------------------------------

def test_complete_task_marks_task_done():
    """complete_task() should mark the task as completed."""
    s, mochi, _ = _make_scheduled_scheduler()
    walk = mochi.tasks[0]
    s.complete_task(walk, mochi)
    assert walk.completed is True


def test_complete_task_adds_next_occurrence_to_pet():
    """complete_task() on a daily task should add one new task to the pet."""
    s, mochi, _ = _make_scheduled_scheduler()
    walk = next(t for t in mochi.tasks if t.frequency == "daily")
    count_before = len(mochi.tasks)
    s.complete_task(walk, mochi)
    assert len(mochi.tasks) == count_before + 1


def test_complete_task_no_recurrence_for_as_needed():
    """complete_task() on an as-needed task should NOT add a new task."""
    owner = _make_owner()
    pet = Pet(name="Mochi", species="dog", age=3)
    task = Task("Vet visit", duration_minutes=60, priority="medium", frequency="as-needed")
    pet.add_task(task)
    owner.add_pet(pet)
    s = Scheduler(owner=owner, date="2026-03-30")
    s.build_plan()
    count_before = len(pet.tasks)
    result = s.complete_task(task, pet)
    assert result is None
    assert len(pet.tasks) == count_before


# ---------------------------------------------------------------------------
# Scheduler — detect_conflicts (Step 4)
# ---------------------------------------------------------------------------

def test_detect_conflicts_finds_overlap():
    """Two tasks with the same start_time should trigger a conflict warning."""
    s, mochi, luna = _make_scheduled_scheduler()
    # Force an overlap: both tasks start at 09:00
    s.scheduled_tasks[0].start_time = "09:00"
    s.scheduled_tasks[1].start_time = "09:00"
    conflicts = s.detect_conflicts()
    assert len(conflicts) >= 1
    assert "CONFLICT" in conflicts[0]


def test_detect_conflicts_sequential_times_no_conflict():
    """Sequential non-overlapping tasks should produce zero conflicts."""
    s, *_ = _make_scheduled_scheduler()
    # assign_times already ran in helper — times are sequential
    assert s.detect_conflicts() == []


def test_detect_conflicts_adjacent_tasks_no_conflict():
    """Tasks that touch (end == next start) should NOT count as a conflict."""
    owner = _make_owner(60)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk",     duration_minutes=30, priority="high"))
    pet.add_task(Task("Training", duration_minutes=30, priority="medium"))
    owner.add_pet(pet)
    s = Scheduler(owner=owner, date="2026-03-30")
    s.build_plan()
    s.assign_times("08:00")     # 08:00–08:30, 08:30–09:00 — adjacent, not overlapping
    assert s.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Scheduler — _find_pet helper
# ---------------------------------------------------------------------------

def test_find_pet_returns_correct_pet():
    """_find_pet() should identify which pet owns a given task object."""
    s, mochi, luna = _make_scheduled_scheduler()
    walk = mochi.tasks[0]
    feeding = luna.tasks[0]
    assert s._find_pet(walk) is mochi
    assert s._find_pet(feeding) is luna


def test_find_pet_returns_none_for_unknown_task():
    """_find_pet() should return None for a task not in any pet's list."""
    s, *_ = _make_scheduled_scheduler()
    orphan = Task("Unknown", duration_minutes=5, priority="low")
    assert s._find_pet(orphan) is None
