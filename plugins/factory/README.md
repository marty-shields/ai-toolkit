# factory

A small pipeline that turns a plan file into a pull request. You plan with Claude until the plan is good, run `/factory:build <plan-file>`, and come back to a PR with a list of questions on it.

## Use it in a repo
1. Install the plugin: `/plugin marketplace add marty-shields/ai-toolkit`, then `/plugin install factory@ai-toolkit`.
2. Write a plan (`skills/build/plan-template.md` is a skeleton).
3. Run `/factory:build path/to/plan.md`. Add run notes after the path to override a default, for example `/factory:build plan.md open as a draft`.

No setup file is needed in the repo. The builder reads the repo's own guidance files (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`), build files, CI workflows and PR template once, and passes a short "repo facts" block to every agent. Anything it cannot find is marked `unknown` and goes on the question list; it never invents a command. The more a repo's `AGENTS.md` or `CLAUDE.md` says about how to build, test and ship, the better the run.

The builder never merges.

## Flow
Preflight (discover the repo, worktree off the default branch) → implement → verify → review 1 (code quality and test quality in parallel) → review 2 (requirements) → review 3 (security) → final verify → PR.

Each review runs once. If it finds something, one fix pass runs and the builder moves on. Anything still open goes on the question list, which is posted as a PR comment. A feature gets code and tests together; a change or bug fix gets a failing test first.

## Parts
| File | Job | Model |
|---|---|---|
| `skills/build/SKILL.md` | The builder: discovers the repo, runs the stages, holds the question list | your session |
| `skills/build/report-format.md` | The short report every agent returns | n/a |
| `agents/implementer.md` | Code and tests; also applies review fixes | sonnet |
| `agents/verifier.md` | Build, tests, then the repo's strategy: api, web, emulator, cli or library | sonnet |
| `agents/review-quality.md` | Code quality, via `/code-review` and the repo's rules | opus |
| `agents/review-tests.md` | Test quality, with a mutation check in a throwaway worktree | opus |
| `agents/review-requirements.md` | Each requirement traced to code and to a test that asserts it | opus |
| `agents/review-security.md` | Security, via `/security-review` | opus |
| `agents/pr-opener.md` | Push, open the PR, post the questions | sonnet |

## Guarantees
- **No silent skips.** A review counts as run only when its report says which skill or checks ran. If one fails to run, the builder fixes the cause and re-runs it once; if it still fails, the PR says "REVIEW DID NOT RUN".
- **Commit identity.** Your git config, else the newest non-bot author on the default branch, noted in the question list. Git config is never changed.
- **Right branch.** `/code-review` and `/security-review` review the branch of their working directory, and a `cd` inside an agent's Bash call does not carry over. The builder creates the worktree itself, then makes the session's working directory the worktree for the review stages: a plain `cd` from the main session carries over when the worktree is inside the folder you started in (a bare-repo layout, the usual case), and `EnterWorktree` covers a start inside another worktree (it isolates git, so it is used for the reviews only). Each skill-calling reviewer checks `pwd` and the branch before calling the skill in-process, and falls back to a nested `claude -p` session inside the worktree if they do not match.

## Tuning
- Change a model: edit `model:` in the agent's frontmatter.
- Drop a stage: delete its step in `skills/build/SKILL.md` and its agent file.
- Add a stage: write an agent that follows `report-format.md`, then add a step to the builder.
