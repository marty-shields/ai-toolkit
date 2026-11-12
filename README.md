# ai-toolkit

My Claude Code plugins and tools.

## Install
```
/plugin marketplace add marty-shields/ai-toolkit
/plugin install factory@ai-toolkit
```
To try it from a local clone: `claude plugin marketplace add /path/to/ai-toolkit`.

## Plugins
| Plugin | What it does |
|---|---|
| [factory](plugins/factory/README.md) | Plan file to pull request: implement with tests, verify, four reviews, final verify, PR with a question list |

## Tools
- [`tools/usage-report.py`](tools/usage-report.py): sums tokens and shows a per-agent timeline and peak context for a Claude Code session and its subagents.

## Licence
[MIT](LICENSE).
