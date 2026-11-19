# Plan: <goal in a few words>

Type: feature | change | bug fix

## Why
<The problem or need, and who it is for.>

## What was decided (don't reopen)
- <Decisions already made with the user.>

## Already true in the code (checked; don't redo)
- <Things you verified exist, with file paths.>

## Requirements
Each is checked by the requirements review, so make them testable.
1. <Behaviour 1>
2. <Behaviour 2>

## Seams and a test per requirement
Where each requirement is tested, agreed before coding so the tests sit at the right level. A seam is the public entry point a test drives: a service or store method, an endpoint, a view model, a component, a CLI command. Prefer the lowest seam that shows the behaviour; use E2E only for what nothing lower can show.

| Req | Seam (type and method, endpoint or screen) | Test (file and name, new or existing) |
|---|---|---|
| 1 | <e.g. `FoodStore.SearchAsync`> | <e.g. `tests/Core/FoodStoreTests.cs` `Search_puts_favourites_first` (new)> |

## Size
Production files expected to change: <number>. If it is more than 5, or the plan changes both core logic and UI screens, split it into smaller plans (an epic runs each as its own task).

## Specification for screens
For each changed screen: what it shows, in which states (empty, filled, error), and light and dark if it matters. Attach a wireframe path or link if there is one.

## Bug reproduction (bug fixes only)
<Steps and what happens now versus what should happen. The first test must fail for this reason.>

## Out of scope
- <What not to touch.>

## May touch (for the gate)
<Only if needed: say so if the change touches `*.razor`, CSS, Stories, `wwwroot`, migrations or the coverage baseline.>

## Done means
- <Observable result, e.g. tests pass, screen matches the spec.>
