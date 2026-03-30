# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Testing PawPal+

### Run the test suite

```bash
# activate your virtual environment first
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pytest tests/ -v
```

### What the tests cover

31 tests across all four core classes and the new scheduling algorithms:

| Category | Tests | Description |
|---|---|---|
| Time helpers | 2 | `_parse_time` / `_format_time` round-trip accuracy |
| Task | 6 | `mark_complete`, idempotency, `next_occurrence` for daily/weekly/as-needed, field preservation |
| Pet | 2 | `add_task` count, `get_tasks_by_priority` ordering |
| Owner | 2 | `add_pet` registration, `get_available_time` |
| Scheduler — build_plan | 3 | Budget cap, priority-first selection, zero-fit case |
| **Sorting correctness** | 4 | `assign_times` sets correct start/sequential times; `sort_by_time` returns chronological order; tasks without times sort last |
| **Filtering** | 4 | Filter by pet name, by completion status, by both combined, and with no filter |
| **Recurrence logic** | 3 | `complete_task` marks done, adds next-day task for daily frequency, adds no task for as-needed |
| **Conflict detection** | 3 | Overlapping tasks flagged, sequential tasks clean, adjacent (touching) tasks not flagged |
| Helper | 2 | `_find_pet` returns correct pet or None |

### Confidence level

⭐⭐⭐⭐⭐ (5/5) — All 31 tests pass. Edge cases covered: zero-budget schedules, as-needed recurrence, adjacent-but-not-overlapping time slots, and tasks with no start time assigned.
