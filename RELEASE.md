# Release process

We cut a release whenever a milestone exits. The bar is small and the
process is automatic.

## When to cut a release

- All issues in the current milestone are closed (or explicitly deferred)
- The CHANGELOG has an entry for the new version
- The test gate is green on `main` (`./run.sh check` exits 0)
- The main branch is at the commit you want to ship (fast-forward, no
  half-baked WIP)

## Versioning

We follow [SemVer](https://semver.org/). Pre-1.0, anything in 0.y.0 is
"feature work landed and tested". The next 0.y.0 is the next milestone.

| Change | Bump |
|--------|------|
| Backward-incompatible engine change | major (0.y -> 0.y+1) |
| New module, new schema table, new CLI subcommand, new LLM provider | minor (0.y.0 -> 0.y.1) |
| Bug fix, doc rewrite, perf tweak | patch (0.y.0.z -> 0.y.0.z+1) |

## How to cut

1. Update `CHANGELOG.md`: move the `Unreleased` section's content into a
   new dated section under the next version.
2. Commit: `chore: cut v0.y.0` (six words, conventional).
3. Tag: `git tag -a v0.y.0 -m "v0.y.0"` and push with `git push origin v0.y.0`.
4. Run `gh release create v0.y.0 --generate-notes` (or paste the CHANGELOG
   section into the release body).
5. Update `CHANGELOG.md` link table so the new version compares to the
   prior one.

## What is *not* in a release

- Spec docs that describe code that hasn't shipped yet (those live in
  `docs/*-spec.md` and are linked from the matching issue, not the
  changelog)
- Internal scripts, refactors with no behavior change
- Things the user can opt into (separate docs)

## Honoring this

The release process is itself documented in `CHANGELOG.md` (see the
"Changelog and release process" line under v0.1.0). The v0.2.0 release
introduced the eval harness and the landing page; the next minor is
whatever ships the M2 spec backlog to runtime.
