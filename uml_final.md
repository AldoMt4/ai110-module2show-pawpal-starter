# PawPal+ — Final Class Diagram

Paste the Mermaid code below into [mermaid.live](https://mermaid.live) to render and export as PNG.

```mermaid
classDiagram
    class Task {
        +str title
        +int duration_minutes
        +str priority
        +str category
        +str frequency
        +bool completed
        +bool is_scheduled
        +str start_time
        +str due_date
        +mark_complete() None
        +next_occurrence(from_date: str) Task
    }

    class Pet {
        +str name
        +str species
        +int age
        +list~Task~ tasks
        +add_task(task: Task) None
        +get_tasks_by_priority() list~Task~
    }

    class Owner {
        +str name
        +int available_minutes
        +list~str~ preferences
        +str day_start
        +list~Pet~ pets
        +add_pet(pet: Pet) None
        +get_available_time() int
        +get_all_tasks() list~Task~
    }

    class Scheduler {
        +Owner owner
        +str date
        +list~Task~ scheduled_tasks
        +build_plan() list~Task~
        +assign_times(day_start: str) None
        +sort_by_time() list~Task~
        +filter_tasks(pet_name, completed) list~Task~
        +complete_task(task, pet) Task
        +detect_conflicts() list~str~
        +_find_pet(task: Task) Pet
        +explain_plan() str
        +get_total_duration() int
    }

    Owner "1" --> "0..*" Pet : has
    Pet "1" --> "0..*" Task : has
    Scheduler --> Owner : uses
    Scheduler --> Pet : calls add_task
    Scheduler ..> Task : schedules / completes
```

## Changes from initial UML (Phase 1)

| What changed | Why |
|---|---|
| `Task` gained `start_time`, `due_date`, `next_occurrence()` | Needed for time-based sorting and recurring task automation |
| `Owner` gained `day_start` | Scheduler needs a reference clock to assign `HH:MM` start times |
| `Scheduler` gained 6 new methods | Sorting, filtering, recurrence, conflict detection, and pet lookup were added as the algorithm layer grew |
| `Scheduler → Pet` (calls `add_task`) | `complete_task()` adds the next recurrence directly to the pet — this relationship was not in the original design |
