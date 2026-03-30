"""
main.py — Demo script for PawPal+ logic layer.
Run with: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler

# --- Owner ----------------------------------------------------------------
jordan = Owner(
    name="Jordan",
    available_minutes=90,
    preferences=["morning walks", "short sessions"],
)

# --- Pets -----------------------------------------------------------------
mochi = Pet(name="Mochi", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# --- Tasks for Mochi ------------------------------------------------------
mochi.add_task(Task("Morning walk",   duration_minutes=30, priority="high",   category="exercise"))
mochi.add_task(Task("Flea treatment", duration_minutes=10, priority="high",   category="health",     frequency="weekly"))
mochi.add_task(Task("Trick training", duration_minutes=20, priority="medium", category="enrichment"))

# --- Tasks for Luna -------------------------------------------------------
luna.add_task(Task("Feeding",          duration_minutes=5,  priority="high",   category="feeding"))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority="medium", category="hygiene"))
luna.add_task(Task("Brush coat",       duration_minutes=15, priority="low",    category="grooming",   frequency="weekly"))

# --- Register pets with owner --------------------------------------------
jordan.add_pet(mochi)
jordan.add_pet(luna)

# --- Build and print schedule --------------------------------------------
scheduler = Scheduler(owner=jordan, date="2026-03-30")
scheduler.build_plan()

print(scheduler.explain_plan())

# --- Mark one task complete and show it updated --------------------------
mochi.tasks[0].mark_complete()
print("(Marking 'Morning walk' as done...)")
print(scheduler.explain_plan())