"""
tests/test_pawpal.py — Basic tests for PawPal+ core classes.
Run with: python -m pytest
"""

from pawpal_system import Owner, Pet, Task, Scheduler


# ---------------------------------------------------------------------------
# Task tests
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


# ---------------------------------------------------------------------------
# Pet tests
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

    sorted_tasks = pet.get_tasks_by_priority()
    priorities = [t.priority for t in sorted_tasks]
    assert priorities == ["high", "medium", "low"]


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_add_pet_registers_pet():
    """add_pet() should add the pet to the owner's pets list."""
    owner = Owner(name="Jordan", available_minutes=60)
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(owner.pets) == 0
    owner.add_pet(pet)
    assert len(owner.pets) == 1
    assert owner.pets[0].name == "Mochi"


def test_get_available_time_returns_budget():
    """get_available_time() should return the owner's available_minutes."""
    owner = Owner(name="Jordan", available_minutes=90)
    assert owner.get_available_time() == 90


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_scheduler_respects_time_budget():
    """build_plan() should not schedule tasks exceeding available_minutes."""
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Walk",     duration_minutes=20, priority="high"))
    pet.add_task(Task("Training", duration_minutes=20, priority="medium"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, date="2026-03-30")
    plan = scheduler.build_plan()

    assert scheduler.get_total_duration() <= 30
    assert len(plan) == 1  # only the first 20-min task fits


def test_scheduler_picks_highest_priority_first():
    """build_plan() should include high-priority tasks before low ones."""
    owner = Owner(name="Jordan", available_minutes=25)
    pet = Pet(name="Luna", species="cat", age=5)
    pet.add_task(Task("Grooming", duration_minutes=20, priority="low"))
    pet.add_task(Task("Feeding",  duration_minutes=5,  priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, date="2026-03-30")
    plan = scheduler.build_plan()

    titles = [t.title for t in plan]
    assert "Feeding" in titles
    assert "Grooming" in titles  # both fit within 25 min


def test_scheduler_excludes_task_that_does_not_fit():
    """build_plan() should skip a task when it alone exceeds remaining time."""
    owner = Owner(name="Jordan", available_minutes=10)
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_task(Task("Long walk", duration_minutes=60, priority="high"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner=owner, date="2026-03-30")
    plan = scheduler.build_plan()

    assert plan == []
    assert scheduler.get_total_duration() == 0
