"""
PawPal+ — logic layer
Four core classes: Task, Pet, Owner, Scheduler
"""

from dataclasses import dataclass, field

# Priority ranking used by sorting logic (lower number = higher priority)
PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task — a single pet care activity
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    category: str = "general"
    frequency: str = "daily"  # "daily" | "weekly" | "as-needed"
    completed: bool = False
    is_scheduled: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True


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
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = preferences or []
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
# Scheduler — builds and explains a daily care plan for the owner
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, date: str) -> None:
        self.owner = owner
        self.date = date
        self.scheduled_tasks: list[Task] = []

    def build_plan(self) -> list[Task]:
        """Select highest-priority tasks that fit within the owner's time budget.

        Resets any previous plan, then greedily picks tasks from the full
        priority-sorted list until available_minutes is exhausted.
        Returns the list of scheduled tasks.
        """
        for task in self.owner.get_all_tasks():
            task.is_scheduled = False
        self.scheduled_tasks = []

        time_remaining = self.owner.get_available_time()
        for task in self.owner.get_all_tasks():
            if task.duration_minutes <= time_remaining:
                task.is_scheduled = True
                self.scheduled_tasks.append(task)
                time_remaining -= task.duration_minutes

        return self.scheduled_tasks

    def explain_plan(self) -> str:
        """Return a formatted, human-readable summary of the scheduled plan.

        Lists every scheduled task with its priority and completion status,
        then reports any tasks skipped due to insufficient time.
        """
        if not self.scheduled_tasks:
            return "No tasks scheduled. Call build_plan() first or add tasks to pets."

        lines: list[str] = [
            f"\n{'=' * 52}",
            f"  Today's Schedule for {self.owner.name}  —  {self.date}",
            f"  Budget: {self.owner.get_available_time()} min  |  "
            f"Planned: {self.get_total_duration()} min",
            f"{'=' * 52}",
        ]
        for i, task in enumerate(self.scheduled_tasks, start=1):
            status = "[done]" if task.completed else "[ ]"
            lines.append(
                f"  {i}. {status} [{task.priority.upper():6}] "
                f"{task.title} ({task.duration_minutes} min)"
            )

        skipped = [t for t in self.owner.get_all_tasks() if not t.is_scheduled]
        if skipped:
            lines.append(f"\n  Skipped (not enough time):")
            for task in skipped:
                lines.append(f"    - {task.title} ({task.duration_minutes} min)")

        lines.append(f"{'=' * 52}\n")
        return "\n".join(lines)

    def get_total_duration(self) -> int:
        """Return the total minutes consumed by all scheduled tasks."""
        return sum(t.duration_minutes for t in self.scheduled_tasks)