## What

One paragraph. What code changes and why.

## Issue

Closes #NNN

## Acceptance criteria

Paste the AC checklist from the linked issue, then tick each with
the evidence: command output, test name, screenshot link, doc
quote. Do not check a box unless you can show it works.

- [ ] ...
- [ ] ...
- [ ] All existing tests stay green (`./run.sh check`).

## Test evidence

```
$ ./run.sh check
... paste output ...
```

If the PR adds new tests, list them and their one-line purpose.

## Process

- [ ] Branch is `issue/NNN-slug` off `main`
- [ ] Subject after the type tag is exactly six words
- [ ] Co-author trailer is present on every commit
- [ ] No live network, no real credentials, no live Reddit fetches
- [ ] No force-push, no direct main commits

## Risks and follow-ups

Anything the reviewer should know about that isn't covered by AC.
