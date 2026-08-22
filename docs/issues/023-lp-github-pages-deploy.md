# Landing page — GitHub Pages deploy pipeline

**Milestone:** ML — Landing Page · **Area:** site · **Size:** S

## Scope
- `.github/workflows/site.yml`: build `site/`, deploy to GitHub Pages on
  merge to main when `site/**` changes; preview comment on PRs.
- Custom 404, cache headers via workflow config.

## Acceptance criteria
- [ ] Site live on Pages URL after merge.
- [ ] PR touching site/** gets an automated preview link.
