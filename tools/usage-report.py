#!/usr/bin/env python3
"""Sum tokens and show a timeline for one Claude Code session and its subagents.

Usage: python3 -I usage-report.py <session path without .jsonl> [-v]
  e.g.  ~/.claude/projects/<project-dir>/<session-id>

Reads <session>.jsonl and <session>/subagents/*.jsonl. For each file it prints the time span,
token totals (deduplicated by message id) and the peak context (the largest single prompt:
input + cache read + cache write). Sessions started by a nested `claude -p` are separate and
are not included; the factory reviewers report their cost themselves.
"""
import glob
import json
import os
import sys
from datetime import datetime


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def scan(path):
    seen, first, last, events = {}, None, None, []
    for line in open(path):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        t = o.get("timestamp")
        if t:
            t = ts(t)
            first = first or t
            last = t
        m = o.get("message") or {}
        if m.get("role") == "assistant" and m.get("usage"):
            seen[m.get("id") or o.get("uuid")] = (m["usage"], m.get("model"))
            for c in m.get("content") or []:
                if c.get("type") == "tool_use" and t:
                    i = c.get("input", {})
                    d = i.get("description") or i.get("skill") or (i.get("command", "")[:70] if c["name"] == "Bash" else "")
                    events.append((t, c["name"], d))
    tot = dict(inp=0, out=0, cr=0, cc=0)
    peak = 0
    for u, _ in seen.values():
        tot["inp"] += u.get("input_tokens", 0)
        tot["out"] += u.get("output_tokens", 0)
        tot["cr"] += u.get("cache_read_input_tokens", 0)
        tot["cc"] += u.get("cache_creation_input_tokens", 0)
        peak = max(peak, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
    tot["peak"] = peak
    return first, last, tot, events, {m for _, m in seen.values()}


def main():
    base = sys.argv[1]
    verbose = "-v" in sys.argv
    rows = [("MAIN", base + ".jsonl")] + [(os.path.basename(p)[:-6], p) for p in sorted(glob.glob(base + "/subagents/*.jsonl"))]
    grand = dict(inp=0, out=0, cr=0, cc=0)
    main_peak = 0
    for name, path in rows:
        f, l, t, ev, models = scan(path)
        for k in grand:
            grand[k] += t[k]
        if name == "MAIN":
            main_peak = t["peak"]
        span = f"{f:%H:%M:%S}-{l:%H:%M:%S} ({(l - f).total_seconds():5.0f}s)" if f and l else "n/a"
        print(f"{name[:26]:26} {span} in={t['inp']} out={t['out']} cacheR={t['cr']} cacheW={t['cc']} peakCtx={t['peak']} {','.join(x or '?' for x in models)}")
        if verbose:
            for e in ev:
                print(f"    {e[0]:%H:%M:%S} {e[1]:8} {e[2]}")
    print("TOTAL", grand, "mainPeakCtx", main_peak)


if __name__ == "__main__":
    main()
