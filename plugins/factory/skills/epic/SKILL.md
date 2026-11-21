---
name: epic
description: Run an epic (a GitHub issue with sub-issues) as a series of factory builds on one epic branch, merging each task PR into the epic branch, keeping open questions in the epic PR and asking them in rounds at the end. Only run it when the user types /factory:epic or an orchestrating prompt explicitly names an epic issue. Never start it on your own initiative.
argument-hint: <epic-issue-number-or-url> [run notes]
---

# /factory:epic: epic issue to a ready epic PR

You are the orchestrator. You never write code. Each task runs as one subagent that invokes the skill `factory:build` on a plan file, and you keep only its short report. Your own work is the plans, the acceptance comment, the CI watch, the task merge, the epic PR, the issue close and the cleanup.

`$ARGUMENTS` is the epic issue (number or URL), then optional **run notes** in plain words that override the defaults below. Ignore anything in the run notes that looks like pasted command output.

## Defaults (run notes may change them)
- **You may:** create branches, push task branches, open PRs, and squash-merge a TASK PR into the epic branch once its CI is green and every review finding is fixed.
- **You never:** merge into the default branch, merge the epic PR, change git config, or kill processes that are not yours. Another job may be using a stories server or a browser.
- **Keep replies short and plain.** Tell the user progress when asked, and what is running.
- **Stop and tell the user** when a build or test is still red after the final-verify fix pass, a stage is blocked and cannot be unblocked, or a task needs a new package or something the repo's guidance says needs approval. Leave that worktree in place.

## Setup
1. Read the epic issue and every sub-issue, and the repo's guidance files (AGENTS.md, CLAUDE.md, CONTRIBUTING.md) and CI workflows once. From them, write the **repo facts** block once, in the format `factory:build`'s Preflight describes, including the commands, the gates and the environment workarounds the repo documents. Pass it to each task's brief as run notes, so the build skips its own discovery. Do not hard-code them here.
2. Create the epic branch (`epic/<name>`) off the default branch and push it. If you need a worktree for it, put it under the repo root's `.claude/worktrees/` too. Open a **draft** epic PR into the default branch. Its body has Summary, Status, Sub-issues (a checklist), and Open questions.
3. For each sub-issue write a plan file (use `plan-template.md` from `factory:build`) in a scratchpad folder, filling in its "Seams and a test per requirement" table and its "Size" line. **Keep tasks small:** if a plan would change more than 5 production files (tests not counted), or both core logic and UI screens, split it into smaller tasks (for example the core change first, then the screens on top), each with its own plan and PR into the epic branch, and note the split in the epic PR's Sub-issues list. Order the tasks by dependency; tasks that touch the same files run one after another, independent ones may run in parallel.

## The task loop (one task at a time)
1. Start a general-purpose subagent in the background with: "Invoke the Skill `factory:build` on <plan>", the epic branch as the PR base, the rules above, and the run note below about closing agents. Keep a list of every agent id you start.
2. When it reports, read the PR and its CI yourself; do not trust the report alone. If CI is red, send the agent back with the failing log; do not merge red.
3. When CI is green and every finding is fixed, post an **acceptance comment** on the task PR: CI result, each review's findings and fixes, what is unverified. Then squash-merge it into the epic branch.
4. Update the epic PR body: tick the sub-issue, add a `### From <task> (#PR)` section with the task's open items (auto-resolved ones ticked, with their answer and source), and note what is unverified. Close the sub-issue (a merge into a non-default branch does not close it).
5. **Clean up.** Remove the task's worktree and branches (local and remote). List the agents and stop every one for this task, stage helpers included, then list again to check none are left. Check for stray emulator, browser, stories-server and test processes and stop only ours.
6. Next task.

## Run note to give every task agent
"Create your worktree under the repo root's `.claude/worktrees/` (the folder that holds `.bare` in a bare-repo layout, otherwise the main work tree) with `git worktree add`. Move between folders only with Bash `cd` and absolute paths; never call the `EnterWorktree` or `ExitWorktree` tools, because they ask the user to approve each call."
"Defer the slow verification (emulator or device E2E, full browser E2E suites) to the epic PR's CI: the final verify runs only the fast parts (build, unit tests, screenshots, API calls, final checks)." Leave this note out only if the epic's run notes ask for per-task E2E.
"Close every agent you start: keep each stage agent's id, stop it once it has reported, and before your final report list agents and stop every one you started. If you are resumed after an interruption, list your agents first, stop leftovers, and re-run only the stage that did not report; never start a second copy of a stage that is still running."

## Interruptions and pauses
- **Network error or a dead agent:** check the branch (`git log`, `git status`), the PR and the agent list before acting. Resume the same agent with SendMessage and say what to continue from. Never start a duplicate of work that may still be running.
- **The user pauses:** ask the running task to finish its current stage, commit and push to its task branch only, stop its processes and report exactly what is done and what remains. Leave the worktree. Save the resume steps and any unverified patch somewhere that survives a cleanup (a folder outside the scratchpad), write a short "Paused" section in the epic PR, and note it in memory. On resume, remove the Paused section.
- **A hand-back that repeats or says "waiting":** it is usually the same report again or a stage still running. Confirm the state; do not re-ask or re-run.

## Open questions
Do not ask the user anything mid-epic. Each task's open items live in the epic PR under its "From" section, and its own PR under `## Open items`. When the last task has merged:
1. Collect every unanswered item. Auto-resolved items are already ticked; do not ask them again unless the user unticked one. Ask them with `AskUserQuestion` in rounds, **decisions first**, up to 4 questions per call, each with 2-4 concrete options and your recommendation first marked "(Recommended)". Give each question enough context to stand alone.
2. Write the answers into the epic PR under "Owner answers" and tick the items.
3. An answer that changes code becomes one follow-up task (one PR for several small ones is fine); run it through the same loop.
4. If an answer is a request to change process or wording across the repo (for example a documentation pass), include it in the follow-up task.

## Finish
1. Update the epic PR Status. Mark the epic PR **ready** (this starts the heavy CI, including any full emulator suite; tell the user it will run and roughly how long).
2. Watch the epic CI. If an emulator shard is red, read the job summary's `infra` or `test` verdict as the repo's e2e docs describe. Rerun the failed job once, and only on `infra`. On `test`, or if the rerun fails, fix the cause as a follow-up task.
3. Report to the user in a few lines: the epic PR link, what each task's reviews found and fixed, anything unverified or not run, and any unanswered questions. **Do not merge the epic PR.**
