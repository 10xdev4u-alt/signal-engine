# Landing page — design system + static scaffold

**Milestone:** ML — Landing Page · **Area:** site · **Size:** M

## Scope
- `site/`: static, dependency-light (no framework unless justified in PR).
- Design system first: type scale, color tokens, spacing rhythm, dark mode —
  documented tokens before components. No creativity or design limits;
  professional, sharp, zero template-smell.
- Sections scaffolded: hero, what-it-does, why-read-only, live-demo slot,
  get-started. Copy placeholders until #022 pipeline lands.

## Acceptance criteria
- [ ] Tokens documented; every component consumes tokens only.
- [ ] Lighthouse ≥95 performance + accessibility on the scaffold.
- [ ] No external JS beyond what the design genuinely needs.
