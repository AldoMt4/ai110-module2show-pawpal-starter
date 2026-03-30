"""
main.py — PawPal+ demo script.
Demonstrates: sorting by time, filtering, recurring tasks, conflict detection.
Run with: python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

SEP = "─" * 56

# ---------------------------------------------------------------------------
# Setup: owner, pets, and tasks added OUT OF ORDER on purpose
# (sorting will fix the display order)
# ---------------------------------------------------------------------------
jordan = Owner(
    name="Jordan",
    available_minutes=90,
    preferences=["morning tasks first"],
    day_start="08:00",
)

mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# Tasks added out of priority/time order — sorting will demonstrate the fix
mochi.add_task(Task("Trick training",  duration_minutes=20, priority="medium", category="enrichment"))
mochi.add_task(Task("Morning walk",    duration_minutes=30, priority="high",   category="exercise",  frequency="daily"))
mochi.add_task(Task("Flea treatment",  duration_minutes=10, priority="high",   category="health",    frequency="weekly"))

luna.add_task(Task("Brush coat",       duration_minutes=15, priority="low",    category="grooming",  frequency="weekly"))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority="medium", category="hygiene"))
luna.add_task(Task("Feeding",          duration_minutes=5,  priority="high",   category="feeding",   frequency="daily"))

jordan.add_pet(mochi)
jordan.add_pet(luna)

# ---------------------------------------------------------------------------
# Step 1: Build plan + assign sequential "HH:MM" start times
# ---------------------------------------------------------------------------
scheduler = Scheduler(owner=jordan, date="2026-03-30")
scheduler.build_plan()
scheduler.assign_times()          # populates task.start_time for every scheduled task

print(scheduler.explain_plan())

# ---------------------------------------------------------------------------
# Step 2a: Sort by time
# Tasks were added out of priority order; after assign_times() the sort
# reflects the actual clock order rather than insertion order.
# ---------------------------------------------------------------------------
print(f"{'SORT BY TIME':^{len(SEP)}}")
print(SEP)
for t in scheduler.sort_by_time():
    print(f"  {t.start_time}  [{t.priority:6}]  {t.title} ({t.duration_minutes} min)")
print()

# ---------------------------------------------------------------------------
# Step 2b: Filter tasks
# ---------------------------------------------------------------------------
print(f"{'FILTER: Mochi — pending only':^{len(SEP)}}")
print(SEP)
for t in scheduler.filter_tasks(pet_name="Mochi", completed=False):
    print(f"  [ ] {t.title} ({t.priority})")
print()

print(f"{'FILTER: all completed tasks (before any completion)':^{len(SEP)}}")
print(SEP)
done = scheduler.filter_tasks(completed=True)
print(f"  {len(done)} completed task(s)\n")

# ---------------------------------------------------------------------------
# Step 3: Recurring tasks
# Completing a daily task auto-creates the next occurrence via timedelta.
# ---------------------------------------------------------------------------
print(f"{'RECURRING TASKS':^{len(SEP)}}")
print(SEP)

walk = next(t for t in mochi.tasks if t.title == "Morning walk")
feeding = next(t for t in luna.tasks if t.title == "Feeding")

print(f"  Completing '{walk.title}' (frequency: {walk.frequency})...")
next_walk = scheduler.complete_task(task=walk, pet=mochi)
if next_walk:
    print(f"  Next '{next_walk.title}' auto-created — due {next_walk.due_date}")

print(f"  Completing '{feeding.title}' (frequency: {feeding.frequency})...")
next_feed = scheduler.complete_task(task=feeding, pet=luna)
if next_feed:
    print(f"  Next '{next_feed.title}' auto-created — due {next_feed.due_date}")
print()

# ---------------------------------------------------------------------------
# Step 4: Conflict detection
# Force two tasks to the same start_time to simulate a scheduling conflict.
# detect_conflicts() returns warning strings rather than crashing.
# ---------------------------------------------------------------------------
print(f"{'CONFLICT DETECTION':^{len(SEP)}}")
print(SEP)

# Manually override two tasks to overlap: both start at 09:00
walk.start_time = "09:00"         # 30-min walk  → 09:00–09:30
feeding.start_time = "09:00"      # 5-min feeding → 09:00–09:05  ← overlaps!

conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No conflicts detected.")
print()

# Restore correct times and re-check — should be clean
scheduler.assign_times()
print("After restoring sequential times:")
conflicts_after = scheduler.detect_conflicts()
print(f"  {len(conflicts_after)} conflict(s) found.\n")
