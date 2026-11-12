# Report format

Every factory agent ends with one report as its final message. No files. Keep it under 40 lines. Never paste whole files or diffs; use `path:line` references.

```
STATUS: pass | findings | fixed | blocked
CHANGED: <files touched, or "none">
FINDINGS:
- [high|med|low] path:line - what is wrong - suggested fix
EVIDENCE: <tests run and result, screenshots taken and what they show, commands and exit codes>
QUESTIONS: <ambiguities you resolved by assuming, and what you assumed; open points the user should answer. "none" if none>
```

- EVIDENCE may include one table of up to 15 lines (for example a requirements traceability table). Keep everything else short.
- `pass`: nothing to fix. `findings`: a reviewer found problems, listed under FINDINGS (it still ran fully). `fixed`: you changed code to resolve findings. `blocked`: you could not finish or the review could not run; say why under FINDINGS. Never use `blocked` for a review that ran and found problems.
- **Never dodge a guard.** If a tool, sandbox or isolation check refuses a command, do not rewrite the command to get around the refusal (for example by obfuscating a path). Run it once in plain form; if it is still refused, say exactly which command was refused and why under FINDINGS, mark that check as not run, and carry on.
- Reviewers report only real problems. No praise, no restating the diff, no style nits that the repo's formatter or CI already enforces.
- Put an issue under QUESTIONS only when a person must decide. If you can decide, decide, state the assumption, and carry on.
