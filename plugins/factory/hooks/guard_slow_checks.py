"""PreToolUse hook: keep E2E and emulator runs in the factory's final verify.

Acts only inside factory subagents (agent_type "factory:<name>"), and lets the
verifier through. Every other session and agent is untouched. Fails open: any
error or unexpected input allows the call.
"""
import json
import re
import sys

ALLOWED = {"factory:verifier"}

# Commands that only read or print; a segment starting with one is never a run.
READERS = {"grep", "egrep", "rg", "cat", "tail", "head", "less", "ls", "find", "sed",
           "awk", "echo", "printf", "wc", "test", "[", "stat", "git", "gh", "cd", "pgrep"}
PREFIXES = {"nohup", "time", "timeout", "env", "exec", "command", "sudo", "xvfb-run", "flock"}
# Fast static checks that only mention E2E in their name or arguments.
NOT_A_RUN = re.compile(r"check|lint|list|--list-tests|--collect-only|--dry-run", re.I)

SLOW = [
    re.compile(r"(^|/)[\w.-]*e2e[\w.-]*\.(sh|ps1)\b", re.I),                  # e2e-local.sh, run-e2e.ps1
    re.compile(r"^(emulator|adb|avdmanager)\b"),                                # Android emulator tools
    re.compile(r"\bplaywright\s+test\b|\bcypress\s+run\b|\bmaestro\s+test\b|\bdetox\s+test\b"),
    re.compile(r"^(dotnet\s+test|npm|npx|yarn|pnpm|pytest|python3?\s+-m\s+pytest|\S*gradlew|mvn|go\s+test)\b.*e2e", re.I),
]


def segments(cmd):
    cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?^\s*\1\s*$", "HEREDOC", cmd, flags=re.S | re.M)  # heredoc bodies are data
    cmd = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "Q", cmd)  # quoted text is data, not commands
    for part in re.split(r"\|\||&&|[;|&\n()]", cmd):
        words = part.strip().split()
        while words and (re.match(r"^\w+=", words[0]) or words[0] in PREFIXES
                         or re.match(r"^-|^\d+[smh]?$", words[0])):
            words.pop(0)
        if words:
            yield " ".join(words)


def slow_segment(cmd):
    for seg in segments(cmd):
        if seg.split()[0].rsplit("/", 1)[-1] in READERS:
            continue
        if NOT_A_RUN.search(seg):
            continue
        if any(p.search(seg) for p in SLOW):
            return seg
    return None


def main():
    try:
        data = json.load(sys.stdin)
        agent = data.get("agent_type") or ""
        if not agent.startswith("factory:") or agent in ALLOWED:
            return 0
        seg = slow_segment((data.get("tool_input") or {}).get("command", ""))
    except Exception:
        return 0
    if not seg:
        return 0
    reason = (f"factory: E2E and emulator runs happen only in the final verify (factory:verifier); "
              f"{agent} may not run `{seg[:120]}`. Run the build and named unit tests instead, "
              f"and leave E2E to the final verify.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
