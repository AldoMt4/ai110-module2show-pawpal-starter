"""
PawPal+ — logic layer
Four core classes: Task, Pet, Owner, Scheduler
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta

# Priority ranking: lower number = higher priority
PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Time helpers (used by Scheduler.assign_times and detect_conflicts)
# ---------------------------------------------------------------------------

def _parse_time(hhmm: str) -> int:
    """Convert 'HH:MM' string to total minutes since midnight."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _format_time(total_minutes: int) -> str:
    """Convert total minutes since midnight back to 'HH:MM' string."""
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


# ---------------------------------------------------------------------------
# Task — a single pet care activity
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    category: str = "general"
    frequency: str = "daily"   # "daily" | "weekly" | "as-needed"
    completed: bool = False
    is_scheduled: bool = False
    start_time: str = ""        # "HH:MM" assigned by Scheduler.assign_times()
    due_date: str = ""          # "YYYY-MM-DD" — when the task is next due

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self, from_date: str) -> Task | None:
        """Return a fresh Task for the next recurrence using timedelta, or None.

        Daily tasks recur tomorrow (timedelta(days=1)).
        Weekly tasks recur in seven days (timedelta(weeks=1)).
        Tasks with frequency 'as-needed' return None.
        """
        if self.frequency == "as-needed":
            return None
        base = date.fromisoformat(from_date)
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            frequency=self.frequency,
            due_date=(base + delta).isoformat(),
        )


# ---------------------------------------------------------------------------
# Pet — one of the owner's pets, owns its own task list
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a care task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks_by_priority(self) -> list[Task]:
        """Return this pet's tasks sorted from highest to lowest priority."""
        return sorted(self.tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))


# ---------------------------------------------------------------------------
# Owner — the human user with a time budget and one or more pets
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: list[str] | None = None,
        day_start: str = "08:00",
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = preferences or []
        self.day_start = day_start      # "HH:MM" when the care day begins
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def get_available_time(self) -> int:
        """Return the number of minutes available for pet care today."""
        return self.available_minutes

    def get_all_tasks(self) -> list[Task]:
        """Collect every task from every pet and return them sorted by priority."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return sorted(all_tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))


# ---------------------------------------------------------------------------
# Scheduler — builds, enriches, and explains a daily care plan
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, date: str) -> None:
        self.owner = owner
        self.date = date
        self.scheduled_tasks: list[Task] = []

    # --- Core plan building -----------------------------------------------

    def build_plan(self) -> list[Task]:
        """Select highest-priority tasks that fit within the owner's time budget.

        Resets any previous plan and start_time assignments, then greedily
        picks tasks from the priority-sorted list until the budget is exhausted.
        """
        for task in self.owner.get_all_tasks():
            task.is_scheduled = False
            task.start_time = ""
        self.scheduled_tasks = []

        time_remaining = self.owner.get_available_time()
        for task in self.owner.get_all_tasks():
            if task.duration_minutes <= time_remaining:
                task.is_scheduled = True
                self.scheduled_tasks.append(task)
                time_remaining -= task.duration_minutes

        return self.scheduled_tasks

    # --- Step 2: Time assignment, sorting, filtering ----------------------

    def assign_times(self, day_start: str | None = None) -> None:
        """Assign sequential 'HH:MM' start times to all scheduled tasks.

        Walks through scheduled_tasks in plan order, computing each task's
        start as the previous task's start_time + duration_minutes.
        """
        cursor = _parse_time(day_start or self.owner.day_start)
        for task in self.scheduled_tasks:
            task.start_time = _format_time(cursor)
            cursor += task.duration_minutes

    def sort_by_time(self) -> list[Task]:
        """Return a copy of scheduled_tasks sorted by start_time.

        Uses a lambda key on 'HH:MM' strings — lexicographic order works
        correctly for zero-padded time strings. Tasks without a time sort last.
        """
        return sorted(
            self.scheduled_tasks,
            key=lambda t: t.start_time if t.start_time else "99:99",
        )

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Filter all owner tasks by pet name and/or completion status.

        Both parameters are optional; pass neither to get every task.
        """
        results: list[Task] = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is None or task.completed == completed:
                    results.append(task)
        return results

    # --- Step 3: Recurring tasks ------------------------------------------

    def complete_task(self, task: Task, pet: Pet) -> Task | None:
        """Mark a task complete and enqueue its next recurrence on the pet.

        Calls task.mark_complete(), then task.next_occurrence() which uses
        timedelta to calculate the next due date. If a new Task is returned,
        it is added to the pet so it appears in future plans.
        """
        task.mark_complete()
        next_task = task.next_occurrence(self.date)
        if next_task:
            pet.add_task(next_task)
        return next_task

    # --- Step 4: Conflict detection ---------------------------------------

    def detect_conflicts(self) -> list[str]:
        """Check for time overlaps among scheduled tasks; return warning strings.

        Lightweight O(n²) pairwise check: two tasks conflict when one starts
        before the other ends. Returns human-readable messages rather than
        raising an exception so the caller can decide how to handle them.
        Only tasks that have a start_time assigned are considered.
        """
        warnings: list[str] = []
        timed = [t for t in self.scheduled_tasks if t.start_time]
        for i, t1 in enumerate(timed):
            for t2 in timed[i + 1:]:
                s1, e1 = _parse_time(t1.start_time), _parse_time(t1.start_time) + t1.duration_minutes
                s2, e2 = _parse_time(t2.start_time), _parse_time(t2.start_time) + t2.duration_minutes
                if s1 < e2 and s2 < e1:     # standard interval-overlap test
                    warnings.append(
                        f"CONFLICT: '{t1.title}' ({t1.start_time}–{_format_time(e1)}) "
                        f"overlaps '{t2.title}' ({t2.start_time}–{_format_time(e2)})"
                    )
        return warnings

    # --- Internal helpers -------------------------------------------------

    def _find_pet(self, task: Task) -> Pet | None:
        """Return the pet that owns this Task object, or None if not found."""
        for pet in self.owner.pets:
            if task in pet.tasks:
                return pet
        return None

    # --- Explanation & totals ---------------------------------------------

    def explain_plan(self) -> str:
        """Return a formatted, human-readable summary of the scheduled plan."""
        if not self.scheduled_tasks:
            return "No tasks scheduled. Call build_plan() first or add tasks to pets."

        lines: list[str] = [
            f"\n{'=' * 58}",
            f"  Today's Schedule for {self.owner.name}  —  {self.date}",
            f"  Budget: {self.owner.get_available_time()} min  |  "
            f"Used: {self.get_total_duration()} min",
            f"{'=' * 58}",
        ]
        for i, task in enumerate(self.scheduled_tasks, start=1):
            time_col = f" {task.start_time}" if task.start_time else "      "
            status = "[done]" if task.completed else "[ ]"
            lines.append(
                f"  {i}.{time_col}  {status} [{task.priority.upper():6}] "
                f"{task.title} ({task.duration_minutes} min)"
            )

        skipped = [t for t in self.owner.get_all_tasks() if not t.is_scheduled]
        if skipped:
            lines.append("\n  Skipped (not enough time):")
            for task in skipped:
                lines.append(f"    - {task.title} ({task.duration_minutes} min)")

        lines.append(f"{'=' * 58}\n")
        return "\n".join(lines)

    def get_total_duration(self) -> int:
        """Return the total minutes consumed by all scheduled tasks."""
        return sum(t.duration_minutes for t in self.scheduled_tasks)