"""Self-healing guard: a repair may change how an element is found, never what a test asserts.

Feed it the diff a healer (Playwright's healer agent, or a person) made to the tests:

    git diff origin/main -- tests/ | python healing/guard.py --log healing-repairs.jsonl

It accepts the diff only if every changed line differs from its original in locators
alone (page.getByRole(...), page.locator(...) and their chains). Anything else,
an assertion, an expected value, a wait, a skipped test, is rejected.
Exit 0 = accepted, 1 = rejected. Self-contained on purpose: copy it into any repo.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone

LOCATOR_START = re.compile(r"\b(?:this\.)?page\s*\.\s*(?:getBy\w+|locator)\s*\(")
CHAIN = re.compile(r"\s*\.\s*(?:or|and|filter|first|last|nth|getBy\w+|locator)\s*\(")
SKIPS = re.compile(r"\btest\.(?:skip|fixme|fail)\b|\.only\s*\(")


def _close_paren(text, i):
    """Index just past the parenthesis that closes the one opened at text[i - 1]."""
    depth, quote = 1, None
    while i < len(text) and depth:
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        i += 1
    return i


def mask_locators(line):
    """Replace every locator expression, chain included, with <LOCATOR>."""
    out, pos = [], 0
    while True:
        m = LOCATOR_START.search(line, pos)
        if not m:
            out.append(line[pos:])
            return "".join(out).strip()
        end = _close_paren(line, m.end())
        while (c := CHAIN.match(line, end)):
            end = _close_paren(line, c.end())
        out.append(line[pos:m.start()] + "<LOCATOR>")
        pos = end


def changed_lines(diff):
    removed, added = [], []
    for line in diff.splitlines():
        if line.startswith(("---", "+++")):
            continue
        if line.startswith("-"):
            removed.append(line[1:])
        elif line.startswith("+"):
            added.append(line[1:])
    return removed, added


def check(diff):
    """Return (accepted, reason, pairs) for a unified diff."""
    removed, added = changed_lines(diff)
    if not removed and not added:
        return True, "no changes", []
    if any(SKIPS.search(l) for l in added):
        return False, "a test was skipped, marked fixme or focused", []
    if len(removed) != len(added):
        return False, "lines were added or removed, not only edited", []
    pairs = list(zip(removed, added))
    for old, new in pairs:
        if mask_locators(old) != mask_locators(new):
            return False, f"change outside a locator: {old.strip()!r} -> {new.strip()!r}", pairs
    return True, f"{len(pairs)} locator repair(s)", pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log", help="append every accepted repair to this JSON Lines file")
    args = parser.parse_args()
    accepted, reason, pairs = check(sys.stdin.read())
    print(("ACCEPTED: " if accepted else "REJECTED: ") + reason)
    if accepted and args.log and pairs:
        with open(args.log, "a") as f:
            for old, new in pairs:
                f.write(json.dumps({
                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "before": old.strip(), "after": new.strip(),
                }) + "\n")
    sys.exit(0 if accepted else 1)


if __name__ == "__main__":
    main()
