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
    priority: str          # "low" | "medium" | "high"
    category: str = "general"
    is_scheduled: bool = False


# ---------------------------------------------------------------------------
# Pet — one of the owner's pets, holds its own task list
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Append a care task to this pet's task list."""
        pass

    def get_tasks_by_priority(self) -> list[Task]:
        """Return this pet's tasks sorted from highest to lowest priority."""
        pass


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
        pass

    def get_available_time(self) -> int:
        """Return the number of minutes available for pet care today."""
        pass


# ---------------------------------------------------------------------------
# Scheduler — builds and explains a daily care plan for the owner
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, date: str) -> None:
        self.owner = owner
        self.date = date
        self.scheduled_tasks: list[Task] = []

    def build_plan(self) -> list[Task]:
        """
        Select and order tasks that fit within available_minutes.
        Tasks should be prioritized highest-first across all pets.
        Returns the list of scheduled tasks.
        """
        pass

    def explain_plan(self) -> str:
        """
        Return a human-readable explanation of the plan:
        which tasks were scheduled, when, and why others were skipped.
        """
        pass

    def get_total_duration(self) -> int:
        """Return the total minutes consumed by all scheduled tasks."""
        pass