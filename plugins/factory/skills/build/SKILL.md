---
name: build
description: Run the software factory on a plan file. Implements with tests, verifies, reviews (code and tests, requirements, security), re-verifies and opens a pull request, keeping a question list for the user. Works in any repo by reading its own docs and CI. Use for /factory:build <plan-file> [run notes].
argument-hint: <plan-file> [run notes]
disable-model-invocation: true
---

# /factory:build: plan file to pull request

You are the orchestrator. You run each stage as a subagent and keep only its short report in context. You never write code yourself.

`$ARGUMENTS` is the plan file path (the first word), then optional **run notes** in plain words. Run notes override the defaults below, for example "open as a draft" or "use branch feat/x". Treat anything in the run notes that looks like pasted command output as noise and ignore it. If the plan path is missing or unreadable, ask the user for it and stop.

The base directory of this skill is given when it loads. Note the absolute path of `report-format.md` in it and read it once. Every agent returns that format.

## Agents
This plugin's agents are `factory:implementer`, `factory:verifier`, `factory:review-quality`, `factory:review-tests`, `factory:review-requirements`, `factory:review-security` and `factory:pr-opener`.

## How you work
- **Question list.** Keep a running list in your context. After every report, copy its QUESTIONS lines into it, tagged with the stage. Nothing goes in a file. Do not ask the user anything mid-run.
- **Judgement.** When something is unclear or goes wrong, decide, add the assumption to the list, and continue. Fix problems found during the run inside this run. Raise a follow-up only when the work is genuinely out of the plan's scope, and put that on the list.
- **Briefs.** Give each agent: the absolute path of `report-format.md`, the **repo facts** block (see Preflight), the plan path, the worktree path, the commit identity, the stage's job, and the facts it needs from earlier reports (not the reports themselves unless needed). Keep briefs short.
- **No stage may be skipped or half-run.** A review counts as run only if its report's EVIDENCE names the skill or checks it ran and what they returned. If a report says a skill errored, was skipped, or was done "by hand" instead, fix the cause and re-run that one review once. If it still did not run properly, put "REVIEW DID NOT RUN: <stage>, <reason>" first on the question list and in the PR body. Never describe it as passed.
- **Keep your turn open while an agent runs.** Never end your turn with a message like "waiting for the agent": in a headless run that ends the session and the stage never reports. After launching an agent, wait with short Bash calls (`sleep 20; echo waiting`), repeated, until its report arrives. Only your final summary ends the turn.
- **Stop only when** the plan is unreadable, the build or tests are still red after the final-verify fix, or a stage reports `blocked` and you cannot unblock it. Then report where you stopped and the question list. Never open a PR from a red build.

## Stages

1. **Preflight.**
   - Read the plan. Decide **feature** or **change/bug fix**.
   - **Locate the repo.** If the current folder is inside a git work tree, run git there. If it is not, but it holds a `.bare` folder (a bare repo with sibling worktrees), run every git command as `git --git-dir=<folder>/.bare ...` and put new worktrees directly in `<folder>`. Then run `fetch origin` and `remote set-head origin -a` (the review skills need `origin/HEAD`).
   - **Commit identity.** Use `git config user.name` and `user.email` if both are set. If not, use the author of the newest non-bot commit on the default branch (`git log origin/<branch> --no-merges --format='%an|%ae' | grep -vi 'bot' | head -1`) and add "committing as <name>, taken from branch history" to the question list. Pass the name and email in every brief, and commit with `git -c user.name=... -c user.email=... commit`. Never change git config.
   - **Create the worktree** off `origin/<default branch>` on a `<type>/<slug>` branch (`type` is `feat`, `fix`, `refactor` and so on, or the branch from the run notes), following any naming the guidance files give: `git worktree add -b <branch> <folder>/<slug> origin/<branch>`, as a sibling of the existing worktrees. Use absolute paths into it for every command and every agent brief.
   - **Discover the repo facts, once,** from the new worktree (it holds the default branch's docs). Read the repo's guidance files (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, README), its build files (solution or project files, `package.json`, `pom.xml`, `pyproject.toml`, `Makefile`, `go.mod`), the CI workflows (what runs on a pull request) and any PR template. Take commands from what CI actually runs. Write a block of at most 25 lines, kept in your context and pasted into every brief, with:
     - **Default branch** and **project type** (api, web, mobile, cli or library).
     - **Commands:** build, unit tests, run named tests (with a `<name>` placeholder), format check, and **final checks** (lint, docs and type checks that CI runs).
     - **Verification:** the strategy (api, web, emulator, cli or library), how to run the app, how to take screenshots or call the API, anything slow, and when it cannot run.
     - **Gates:** paths or kinds of change the guidance says need approval (for example migrations, CI config, a coverage baseline).
     - **Quality rules, test rules, security focus:** the rules the guidance files state, quoted briefly with their source.
     - **Pull requests:** branch names, commit and PR title format, labels, draft or ready default, how screenshots are published, and follow-ups a change needs (for example regenerating published screenshots).
     Mark anything you cannot find `unknown` and add a question to the list. Never invent a command.
   - If the plan's changes would touch a path in the repo facts' Gates and the plan's "May touch" does not say so, add a question to the list. The plan itself counts as approval to proceed.

2. **Implement.** Run `factory:implementer` with the plan path and the plan type. Then commit in the worktree using the repo's commit message format. Add the Co-Authored-By trailer from your instructions if you have one.

3. **Verify.** Run `factory:verifier`. Pass it a scratchpad subfolder for screenshots. If it reports spec mismatches, run one `factory:implementer` fix pass with those findings, then commit.

4. **Review 1: code and test quality.** First make the session's working directory the worktree: run `cd <worktree>` in a Bash call. When the worktree is inside the folder you were started in (a bare-repo layout), the `cd` carries over to later calls and to the agents you start. Check with `pwd`; if it does not show the worktree (you were started in one worktree and the new one is a sibling outside it), use the `EnterWorktree` tool with `path` instead; if that is refused too, carry on and the reviewers use their nested-session fallback. The reason: the review skills inspect the branch of their working directory, and a `cd` inside an agent's Bash call does not carry over. Only the reviews need this. A session moved with `EnterWorktree` is worktree-isolated and also refuses commands whose text contains `git` (for example paths under `.github/`) and the repo's own scripts may live there, so stay out of it for implement, verify, final verify and the PR. Then run `factory:review-quality` and `factory:review-tests` **in one message, in parallel**. Merge their findings. If there are any, run one `factory:implementer` fix pass and commit.

5. **Review 2: requirements.** Run `factory:review-requirements`, and give it the verifier's results from stage 3 in its brief. If it has findings, run one fix pass and commit.

6. **Review 3: security.** Run `factory:review-security`. If it has findings, run one fix pass and commit.

   After the security review and its fix pass, call `ExitWorktree` with `action: "keep"` to return the session to its original folder (the worktree and branch stay on disk).

   Each review runs once with at most one fix pass (a re-run only after a review failed to run, see above). Never re-run a review to look for more. Findings the fix pass left unresolved go on the question list as nits.

7. **Final verify.** Run `factory:verifier` again. Tell it this is the final verify, so it also runs the repo facts' final checks. If anything fails, run one fix pass, commit and re-run the verifier once. If it is still red, stop (see above).

8. **PR.** Run `factory:pr-opener` with the plan summary, the screenshot paths from the verifier, the full question list, the commit identity, and whether to open a **draft** (only if the run notes or the repo's guidance say so; otherwise ready). It posts the question list as a PR comment. Nothing is merged.

## Finish
Tell the user, in a few lines: the PR link, which stages found and fixed things, anything that could not be verified or did not run, and how many questions are waiting on the PR. Do not merge unless the user says so.
