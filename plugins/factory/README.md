# factory

A small pipeline that turns a plan file into a pull request. You plan with Claude until the plan is good, run `/factory:build <plan-file>`, and come back to a PR with its open items in the description and a round of questions waiting for you.

## Use it in a repo
1. Install the plugin: `/plugin marketplace add marty-shields/ai-toolkit`, then `/plugin install factory@ai-toolkit`.
2. Write a plan (`skills/build/plan-template.md` is a skeleton).
3. Run `/factory:build path/to/plan.md`. Add run notes after the path to override a default, for example `/factory:build plan.md open as a draft`.

No setup file is needed in the repo. The builder reads the repo's own guidance files (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`), build files, CI workflows and PR template once, and passes a short "repo facts" block to every agent. Anything it cannot find is marked `unknown` and goes on the question list; it never invents a command. The more a repo's `AGENTS.md` or `CLAUDE.md` says about how to build, test and ship, the better the run.

The builder never merges.

## Running from a subagent or epic runner
`/factory:build` can also be started by a subagent through the Skill tool, for example one per item of an epic. Requirements: the subagent must run in the foreground. Background subagents don't get the `Agent` tool, which the builder needs to start its stage agents. A subagent spawned from your main conversation defaults to background, so ask for foreground explicitly when you spawn it (for example "run this in the foreground"). The subagent depth limit allows two more layers below it (default 3 is fine; see `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). Subagents cannot ask questions, so the question round is skipped: open items stay unchecked in the PR description and are returned in the final message.

## Running a whole epic
`/factory:epic <epic-issue>` runs an epic as a series of builds on one epic branch: a plan per sub-issue, one `factory:build` agent per task, an acceptance comment and a squash-merge of each task PR into the epic branch, and cleanup of the worktree, branches, processes and every helper agent. Open questions are kept in the epic PR and asked in rounds at the end, with answers written back. It marks the epic PR ready and reports, and never merges it.

## Flow
Preflight (discover the repo, worktree off the default branch) → implement (code, tests and a self-check against the reviewers' lists) → reviews (code quality, test quality, requirements and security, all four in parallel) → one fix pass → final verify (build, full tests, screenshots or API calls, emulator or browser E2E, final checks) → resolve open items → PR → question round.

**Each test tier runs once.** While working, the implementer and fix passes run only the named tests for the code they change. The implementer runs the build and full unit suite once before it reports, and that result is the baseline the reviewers use instead of re-running the suite. E2E and emulator runs happen only at the final verify, and a hook enforces it (see below).

Each review runs once, and their findings go to one combined fix pass. Anything still open goes on the question list. The resolver then settles the assumptions and nits that a written source already answers (the plan, the repo's guidance files, or your `Answer:` lines on earlier PRs), with a verbatim quote the builder checks. It never settles decisions. The PR description lists open items under "Open items" and the settled ones, ticked with their source, under "Auto-resolved", so you can override them. When the PR is open, the builder asks you every remaining item one question at a time (`AskUserQuestion`), then ticks them off and records your answers in the description. In a headless run the items simply stay unchecked. A feature gets code and tests together; a change or bug fix gets a failing test first.

## Parts
| File | Job | Model |
|---|---|---|
| `skills/build/SKILL.md` | The builder: discovers the repo, runs the stages, holds the question list | your session |
| `skills/build/report-format.md` | The short report every agent returns | n/a |
| `agents/implementer.md` | Code and tests, with a self-check against the reviewers' lists; also applies review fixes | sonnet |
| `agents/verifier.md` | The one verify, after the reviews: build, full tests, the repo's strategy (api, web, emulator, cli or library) and final checks; builds missing states in a throwaway copy | sonnet |
| `agents/review-quality.md` | Code quality, via `/code-review` and the repo's rules | opus |
| `agents/review-tests.md` | Test quality, with a mutation check in a throwaway worktree | opus |
| `agents/review-requirements.md` | Each requirement traced to code and to a test that asserts it | opus |
| `agents/review-security.md` | Security, via `/security-review` | opus |
| `agents/resolver.md` | Settles assumptions and nits a quoted source already answers; never decisions | opus |
| `hooks/hooks.json`, `hooks/guard_slow_checks.py` | Blocks E2E and emulator commands in every factory agent except the verifier | n/a |
| `agents/pr-opener.md` | Push, open the PR, write the open items into its description | sonnet |

## Guarantees
- **No sleep polling.** The builder starts stage agents in the foreground, so each Agent call returns the report (it falls back to `sleep 60` waits only if an agent was forced into the background). Agents start long commands in the background and wait with one call that blocks up to 170 s until the command's exit line appears, instead of repeated fixed sleeps.
- **E2E only at the final verify.** `hooks/hooks.json` runs `hooks/guard_slow_checks.py` before every Bash call. Inside a factory agent other than `factory:verifier` it denies commands that run E2E or emulator tools (an `*e2e*.sh` runner, `emulator`, `adb`, Playwright, Cypress, Maestro, Detox, or a test command aimed at an E2E project) and tells the agent why. It ignores every session and agent outside the factory, skips quoted text, heredocs and check or list commands, and lets the call through on any error. Plugin agents cannot carry their own hooks, so this is a plugin hook that reads `agent_type`.
- **No silent skips.** A review counts as run only when its report says which skill or checks ran. If one fails to run, the builder fixes the cause and re-runs it once; if it still fails, the PR says "REVIEW DID NOT RUN".
- **Commit identity.** Your git config, else the newest non-bot author on the default branch, noted in the question list. Git config is never changed.
- **Right branch.** `/code-review` and `/security-review` review the branch of their working directory, and a `cd` inside an agent's Bash call does not carry over. The builder creates the worktree itself with `git worktree add` under the repo root's `.claude/worktrees/` (the folder holding `.bare`, or the main work tree), then runs a plain `cd` into it for the review stages. From a main session that `cd` carries over to the review agents, which call the skill in-process. In a subagent (every epic task) it does not, so each skill-calling reviewer checks `pwd` and the branch and falls back to a nested `claude -p` session started with `cd <worktree>`. The plugin never uses the `EnterWorktree` or `ExitWorktree` tools, because each call asks the user for approval.

## Tuning
- Change a model: edit `model:` in the agent's frontmatter.
- Drop a stage: delete its step in `skills/build/SKILL.md` and its agent file.
- Add a stage: write an agent that follows `report-format.md`, then add a step to the builder.
