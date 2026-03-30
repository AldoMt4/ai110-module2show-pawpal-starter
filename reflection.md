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

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
