# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I designed four classes for PawPal+:

- **Task** (dataclass): Represents a single pet care activity. Holds `title`, `duration_minutes`, `priority` (low/medium/high), `category`, and `is_scheduled`. Using a dataclass keeps it lightweight and easy to compare or sort. Its sole responsibility is to describe *what* needs to be done and how costly it is in time.

- **Pet** (dataclass): Represents one of the owner's pets. Holds `name`, `species`, `age`, and a list of `Task` objects. Responsible for storing its own task list and for sorting those tasks by priority when asked. A Pet knows about its care needs but has no scheduling authority.

- **Owner**: Represents the human user. Holds `name`, `available_minutes` for the day, a list of `preferences` (e.g., "prefer morning walks"), and a list of `Pet` objects. Responsible for tracking the owner's time budget and registering pets. Owner does not build plans — it only describes the constraints.

- **Scheduler**: Orchestrates the daily plan. Takes an `Owner` and a `date`, collects tasks from all pets, selects tasks that fit within `available_minutes` (highest priority first), and can explain the plan in plain language. This is the only class with scheduling authority.

Relationships: Owner has 0..* Pets (one-to-many aggregation); Pet has 0..* Tasks (one-to-many composition); Scheduler depends on Owner (uses-relationship) and produces/marks Tasks as scheduled.

**b. Design changes**

Yes, the design changed in three meaningful ways during implementation:

1. **Task gained `start_time` and `due_date` fields.** The initial design treated tasks as timeless activities — just a duration and a priority. Once I added `assign_times()` to the Scheduler, each task needed to carry its `HH:MM` slot so sorting and conflict detection could work. `due_date` was needed for recurring tasks to know *when* the next occurrence is due.

2. **Owner gained `day_start`.** Initially the Scheduler had no concept of what time the day began. When I added time-slot assignment I realized the reference clock ("08:00") belonged on the Owner, not hardcoded in the Scheduler. This made the parameter user-configurable from the UI.

3. **Scheduler gained a `complete_task()` method and a `_find_pet()` helper.** Originally the UI called `task.mark_complete()` directly. Once recurring tasks were added, that was not enough — the system also needed to add the next occurrence to the correct pet. Centralizing this in `Scheduler.complete_task()` kept the UI clean and the recurrence logic in one place.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers two constraints:

- **Time budget** (`available_minutes`): the hard constraint. A task is only scheduled if it fits in the remaining time.
- **Priority** (`high` / `medium` / `low`): the ordering constraint. All tasks are sorted by priority before the greedy selection loop runs, so high-priority tasks are always considered first.

I decided that *time* was the hard constraint and *priority* was the soft ordering because the opposite would be worse: scheduling a low-priority task and then running out of time for a high-priority one would leave the pet's critical needs unmet.

**b. Tradeoffs**

The scheduler uses a **greedy first-fit approach**: it takes tasks in priority order and adds each one if it fits. This means it can miss a combination that would actually fit more total work. For example, if a 30-minute high-priority task and two 15-minute medium tasks are available in a 30-minute budget, the greedy algorithm takes only the high-priority task, even though the two medium tasks together would also fill the budget and might be more useful.

This tradeoff is reasonable for pet care because: (1) the budget is usually large enough that the greedy approach fills it well, (2) correctness for high-priority tasks (feeding, medication) matters more than maximizing total tasks completed, and (3) a greedy algorithm is easy for a user to reason about — "it just picks the most important things first."

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used at every phase:

- **Design brainstorming (Phase 1)**: Used chat to generate the initial Mermaid class diagram and suggest which responsibilities belonged on which class. The most helpful prompt format was: *"I'm designing a pet care app with these four classes — what methods should each one have and how should they interact?"*
- **Skeleton generation (Phase 2)**: Used inline chat to generate empty method stubs from the UML. This was faster than typing them manually and ensured the signatures matched the diagram.
- **Algorithm implementation (Phase 4)**: Used agent mode to implement `assign_times`, `detect_conflicts`, and `next_occurrence`. The most useful prompts were specific: *"Write a Python method that detects overlapping time intervals and returns warning strings rather than raising exceptions."*
- **Test generation (Phase 5)**: Used the generate-tests action to draft initial test functions, then reviewed and added edge-case tests (adjacent intervals, as-needed recurrence) manually.

**b. Judgment and verification**

When AI generated the initial `detect_conflicts()` method, it used a `datetime` object for time comparisons instead of plain integers. I rejected this because it introduced an unnecessary import and made the code harder to read — the comparison logic is simpler when times are just integers (minutes since midnight). I replaced it with `_parse_time()` / `_format_time()` helpers and verified the interval-overlap condition (`s1 < e2 and s2 < e1`) manually against three test cases: full overlap, partial overlap, and adjacent-but-not-overlapping. The adjacent case (`e1 == s2`) was the trickiest — I confirmed it should *not* count as a conflict and wrote a specific test for it.

---

## 4. Testing and Verification

**a. What you tested**

The 31-test suite covers:

- **Sorting correctness**: `assign_times` sets the first task to `day_start` and each subsequent task immediately after the previous one ends. `sort_by_time` returns tasks in chronological order using the `HH:MM` string key.
- **Recurrence logic**: `next_occurrence` returns a task due tomorrow for daily frequency and in 7 days for weekly (verified exact dates). `complete_task` adds the new task to the pet's list and returns `None` for `as-needed` tasks.
- **Conflict detection**: Overlapping tasks produce a `CONFLICT:` warning string. Sequential tasks produce none. Adjacent tasks (where one ends exactly when the next begins) produce none — this edge case is important because `assign_times` always produces adjacent tasks.
- **Budget cap**: The scheduler never exceeds `available_minutes`. A single task that is larger than the entire budget produces an empty plan.

These tests matter because they verify the *algorithm's reasoning*, not just the data structure. A test that only checks `len(pet.tasks) == 1` after `add_task()` is easy to write but does not verify that the scheduler makes correct decisions under constraints.

**b. Confidence**

Confidence: ⭐⭐⭐⭐⭐ (5/5) for the core scheduling algorithm. The greedy selection, time assignment, conflict detection, and recurrence are all covered by dedicated tests with edge cases.

Edge cases I would test next with more time:
- A task whose duration equals exactly the remaining budget (boundary condition)
- An owner with zero pets or zero tasks (graceful empty-state handling)
- Two pets with tasks of the same priority — verifying the tie-breaking behavior is stable
- Recurrence across a month boundary (e.g., completing a weekly task on March 28 should produce April 4, not a broken date)

---

## 5. Reflection

**a. What went well**

The clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`) worked well throughout the project. Because `Scheduler` is a self-contained object stored in `st.session_state`, adding new methods (like `filter_tasks` or `detect_conflicts`) required zero changes to the session-state structure — the UI just called the new method. This separation made every phase feel incremental rather than disruptive.

**b. What you would improve**

The scheduling algorithm is greedy and does not backtrack. In a future iteration I would explore a knapsack-style optimizer that finds the combination of tasks that maximizes total priority score within the budget, rather than just taking the highest-priority tasks in order. I would also add a `time_of_day` preference to Task (e.g., "morning only") so the scheduler could respect that Mochi needs her walk before 9 AM.

**c. Key takeaway**

The most important thing I learned is that **AI is most useful when you have a clear design first**. When I asked AI to generate a method without specifying the interface, I often got something that worked but did not fit the architecture — like using `datetime` instead of integer minutes, or putting scheduling logic inside `Pet` instead of `Scheduler`. When I came to AI with a precise question ("write this specific method with this signature that returns this type"), the output was nearly always usable. The design work is still the human's job; AI accelerates the implementation once the design is clear.
