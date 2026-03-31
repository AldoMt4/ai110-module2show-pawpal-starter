"""
app.py — PawPal+ Streamlit UI wired to the backend logic layer.

Key pattern: st.session_state acts as a persistent "vault" that survives
reruns. The Owner object (and all Pets/Tasks nested inside it) lives in
st.session_state.owner so it is never recreated from scratch on each click.
"""

# Step 1: Import backend classes — bridges the UI and logic layers
import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planning assistant")

# ---------------------------------------------------------------------------
# Step 2: Session-state bootstrap
#
# Streamlit reruns this file top-to-bottom on every interaction.
# "if key not in st.session_state" guards ensure we only *create* the
# Owner once — subsequent reruns find it already in the vault and skip.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None           # holds the Owner instance
if "last_plan" not in st.session_state:
    st.session_state.last_plan = []         # holds the most recent scheduled tasks
if "last_scheduler" not in st.session_state:
    st.session_state.last_scheduler = None  # holds Scheduler for complete_task()

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.header("1. Owner Setup")

with st.form("owner_form"):
    # Pre-fill from existing session data if the owner already exists
    existing = st.session_state.owner
    owner_name = st.text_input("Your name", value=existing.name if existing else "Jordan")
    col_a, col_b = st.columns(2)
    with col_a:
        available_minutes = st.number_input(
            "Minutes available today",
            min_value=10, max_value=480,
            value=existing.available_minutes if existing else 90,
            step=10,
        )
    with col_b:
        day_start = st.text_input(
            "Day start time (HH:MM)",
            value=existing.day_start if existing else "08:00",
            help="When your pet care day begins, e.g. 08:00",
        )
    saved = st.form_submit_button("Save owner")

if saved:
    if st.session_state.owner is None:
        # First save: create the Owner and store it in session_state
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=int(available_minutes),
            day_start=day_start,
        )
    else:
        # Subsequent save: update the existing Owner in-place so pets are kept
        st.session_state.owner.name = owner_name
        st.session_state.owner.available_minutes = int(available_minutes)
        st.session_state.owner.day_start = day_start
    st.success(f"Owner saved: **{owner_name}** ({available_minutes} min, starts {day_start})")

if st.session_state.owner:
    o = st.session_state.owner
    st.caption(f"Active owner: **{o.name}** — {o.available_minutes} min budget, starts {o.day_start} — {len(o.pets)} pet(s)")

st.divider()

# Guard: nothing below makes sense without an owner
if st.session_state.owner is None:
    st.info("Fill in your owner profile above to get started.")
    st.stop()

owner: Owner = st.session_state.owner   # convenient alias

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# Calls owner.add_pet() — the same method we wrote in pawpal_system.py
# ---------------------------------------------------------------------------
st.header("2. Add a Pet")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    existing_names = [p.name.lower() for p in owner.pets]
    if pet_name.strip().lower() in existing_names:
        st.warning(f"A pet named '{pet_name}' already exists.")
    elif not pet_name.strip():
        st.warning("Pet name cannot be empty.")
    else:
        # Wire UI → backend: call the actual Owner method
        owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
        st.success(f"Added **{pet_name}** the {species}!")

if owner.pets:
    st.caption("Registered pets: " + ", ".join(
        f"**{p.name}** ({p.species}, {p.age}yr)" for p in owner.pets
    ))

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a task to a specific pet
# Calls pet.add_task() — the same method we wrote in pawpal_system.py
# ---------------------------------------------------------------------------
st.header("3. Add a Task")

if not owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        pet_choice = st.selectbox("Assign to pet", [p.name for p in owner.pets])
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox(
                "Category",
                ["exercise", "feeding", "health", "grooming", "enrichment", "hygiene", "other"],
            )
        with col5:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        add_task = st.form_submit_button("Add task")

    if add_task:
        if not task_title.strip():
            st.warning("Task title cannot be empty.")
        else:
            # Find the right pet and call pet.add_task()
            target = next(p for p in owner.pets if p.name == pet_choice)
            target.add_task(Task(
                title=task_title.strip(),
                duration_minutes=int(duration),
                priority=priority,
                category=category,
                frequency=frequency,
            ))
            st.success(f"Added '**{task_title}**' to {pet_choice}.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — View all pets and their tasks
# ---------------------------------------------------------------------------
st.header("4. Pets & Tasks")

if not owner.pets:
    st.info("No pets registered yet.")
else:
    for pet in owner.pets:
        label = f"{pet.name}  ({pet.species}, age {pet.age})  — {len(pet.tasks)} task(s)"
        with st.expander(label, expanded=True):
            if not pet.tasks:
                st.caption("No tasks yet.")
            else:
                rows = [
                    {
                        "Task": t.title,
                        "Min": t.duration_minutes,
                        "Priority": t.priority,
                        "Category": t.category,
                        "Frequency": t.frequency,
                        "Done": "✓" if t.completed else "",
                    }
                    for t in pet.tasks
                ]
                st.table(rows)

st.divider()

# ---------------------------------------------------------------------------
# Section 5 — Generate and display the schedule
# Scheduler.build_plan() is called here and the plan is stored in
# session_state so it survives reruns (e.g. when marking tasks done).
# ---------------------------------------------------------------------------
st.header("5. Generate Schedule")

all_tasks = owner.get_all_tasks()
total_task_min = sum(t.duration_minutes for t in all_tasks)

if not all_tasks:
    st.info("Add at least one task before generating a schedule.")
else:
    col_a, col_b = st.columns(2)
    col_a.metric("Tasks available", len(all_tasks))
    col_b.metric("Total task time", f"{total_task_min} min")

    if st.button("Generate schedule", type="primary"):
        _sched = Scheduler(owner=owner, date=date.today().isoformat())
        _sched.build_plan()
        _sched.assign_times()                              # assign HH:MM start times
        st.session_state.last_plan = _sched.scheduled_tasks
        st.session_state.last_scheduler = _sched          # store for complete_task()

    # Show the plan whenever one exists (persists across reruns)
    if st.session_state.last_plan:
        plan = st.session_state.last_plan
        sched: Scheduler = st.session_state.last_scheduler
        used = sum(t.duration_minutes for t in plan)
        skipped = [t for t in all_tasks if not t.is_scheduled]

        st.success(
            f"Scheduled **{len(plan)}** of {len(all_tasks)} task(s) "
            f"— {used} / {owner.available_minutes} min used"
        )

        # --- Conflict warnings — displayed prominently so they are hard to miss ---
        conflicts = sched.detect_conflicts()
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} schedule conflict(s) detected — review before starting!")
            for w in conflicts:
                st.warning(f"**{w}**  \n_Tip: adjust task durations or regenerate the schedule._")

        # --- Time budget progress bar ---
        done_count = sum(1 for t in plan if t.completed)
        st.progress(
            done_count / len(plan),
            text=f"Daily progress: {done_count} / {len(plan)} tasks completed",
        )

        # --- Today's plan table (sorted by start time, includes Time column) ---
        st.subheader("Today's Plan")
        plan_rows = [
            {
                "#": i,
                "Time": t.start_time or "—",
                "Task": t.title,
                "Priority": t.priority,
                "Duration (min)": t.duration_minutes,
                "Category": t.category,
                "Status": "✓ Done" if t.completed else "Pending",
            }
            for i, t in enumerate(sched.sort_by_time(), start=1)
        ]
        st.table(plan_rows)

        # --- Filter view — exposes filter_tasks() to the user ---
        with st.expander("Filter tasks"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_pet = st.selectbox("By pet", ["All"] + [p.name for p in owner.pets])
            with col_f2:
                filter_status = st.selectbox("By status", ["All", "Pending", "Done"])
            fp = None if filter_pet == "All" else filter_pet
            fc = None if filter_status == "All" else (filter_status == "Done")
            filtered = sched.filter_tasks(pet_name=fp, completed=fc)
            if filtered:
                st.table([
                    {"Task": t.title, "Priority": t.priority,
                     "Duration": f"{t.duration_minutes} min",
                     "Frequency": t.frequency, "Done": "✓" if t.completed else ""}
                    for t in filtered
                ])
            else:
                st.info("No tasks match that filter.")

        # --- Skipped tasks ---
        if skipped:
            with st.expander(f"Skipped ({len(skipped)} task(s) — not enough time)"):
                for t in skipped:
                    st.write(f"- **{t.title}** — {t.duration_minutes} min ({t.priority} priority)")

        # --- Mark tasks complete (uses complete_task for automatic recurrence) ---
        st.subheader("Mark Tasks Complete")
        any_pending = any(not t.completed for t in plan)
        if not any_pending:
            st.balloons()
            st.success("All tasks for today are done — great job!")
        else:
            for t in plan:
                if t.completed:
                    st.write(f"✓ ~~{t.title}~~")
                else:
                    if st.button(f"Mark done: {t.title}", key=f"done_{id(t)}"):
                        pet = sched._find_pet(t)
                        if pet:
                            # complete_task marks done + enqueues next recurrence
                            next_task = sched.complete_task(t, pet)
                            if next_task:
                                st.toast(
                                    f"Next '{t.title}' scheduled for {next_task.due_date}",
                                    icon="🔁",
                                )
                        else:
                            t.mark_complete()
                        st.rerun()