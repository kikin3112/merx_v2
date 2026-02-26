# 09 — Change Policy (Trunk-Based Development)

> How code changes are proposed, validated, and integrated into the MERX v2 codebase.

---

## Philosophy

**"Protect main with automation, not discipline."**

We follow **Trunk-Based Development** (used by Google, Netflix, Meta, Spotify) — the industry standard for modern SaaS with continuous deployment. Every change is validated automatically before it can touch the main branch.

---

## Core Rule

> **No direct commits to `main`. Ever. No exceptions.**

All changes flow through short-lived feature branches → Pull Request → automated CI/CD validation → peer review → merge.

---

## Change Flow

```
1. CREATE branch       →  git checkout -b feat/short-description
2. DEVELOP on branch   →  Small, focused commits. Branch lives < 2 days.
3. PUSH & open PR      →  Pull Request against main
4. AUTOMATED GATES     →  CI/CD runs ALL checks (blocking):
   ├── Lint + type-check
   ├── Unit tests
   ├── Integration tests
   ├── Security: SAST (Semgrep + Bandit)
   ├── Security: SCA (dependency scan)
   ├── Security: Secrets (Gitleaks)
   ├── Security: Container (Trivy) [if applicable]
   ├── Build verification
   └── Coverage check (must not decrease)
5. PEER REVIEW         →  ≥ 1 approval required (2 for critical paths)
6. MERGE               →  Squash merge to main (clean history)
7. AUTO-DELETE branch   →  Feature branch deleted after merge
8. AUTO-DEPLOY          →  Staging auto-deploy → smoke tests
9. RELEASE              →  Release Committee Go/No-Go → production
```

---

## Branch Rules

| Rule | Enforcement |
|------|-------------|
| `main` is protected | GitHub branch protection — cannot push directly |
| All changes via PR | Enforced by GitHub settings |
| CI must pass | PR cannot merge with failing checks |
| Review required | ≥ 1 approval (2 for `auth`, `tenants`, security-related) |
| Squash merge only | Clean, linear history on main |
| Auto-delete branches | After merge, branch is automatically removed |
| Branch naming | `feat/`, `fix/`, `hotfix/`, `chore/`, `docs/` prefixes |

---

## Branch Naming Convention

| Prefix | Use For | Example |
|--------|---------|---------|
| `feat/` | New features | `feat/pos-payment-methods` |
| `fix/` | Bug fixes | `fix/invoice-tax-calculation` |
| `hotfix/` | Critical production fixes | `hotfix/auth-jwt-expiry` |
| `chore/` | Maintenance, deps, CI | `chore/update-semgrep-rules` |
| `docs/` | Documentation only | `docs/api-endpoints-swagger` |
| `refactor/` | Code restructuring | `refactor/tenant-service-split` |

---

## Branch Lifespan Rules

| Type | Max Lifespan | If Exceeds |
|------|-------------|------------|
| `feat/` | 2 days | Split into smaller PRs |
| `fix/` | 1 day | Escalate blocker |
| `hotfix/` | 4 hours | War room mode |
| `chore/` | 1 day | — |
| `docs/` | 1 day | — |

**Why short-lived?** Long-lived branches = merge conflicts + integration pain + hidden risk. The shorter the branch, the easier the merge, the faster the feedback.

---

## Commit Message Convention

```
<type>(<scope>): <short description>

[optional body: explain WHY, not WHAT]

[optional footer: BREAKING CHANGE, refs #issue]
```

**Examples**:
```
feat(invoices): add DIAN electronic billing support
fix(inventory): correct stock deduction on POS return
hotfix(auth): patch JWT refresh token vulnerability
chore(ci): add Trivy container scanning to pipeline
docs(api): update swagger for v2 endpoints
```

---

## Pull Request Requirements

### PR Template

```markdown
## What
[Brief description of the change]

## Why
[Business/technical reason — link to issue/story]

## How
[Technical approach taken]

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests (if cross-module)
- [ ] Manual testing done
- [ ] Security implications considered

## Screenshots (if UI change)
[Before/After]
```

### PR Size Guidelines

| Size | Lines Changed | Guidance |
|------|--------------|----------|
| 🟢 Small | < 100 | Ideal. Fast to review |
| 🟡 Medium | 100-300 | Acceptable. Provide clear description |
| 🔴 Large | 300+ | Split into smaller PRs. Exception: migrations, generated code |

---

## Automated CI/CD Gates (Blocking)

Every PR must pass ALL of these before merge is allowed:

| Gate | Tool | What It Validates |
|------|------|------------------|
| Lint | ESLint / Ruff | Code style and formatting |
| Type Check | TypeScript / mypy | Type safety |
| Unit Tests | pytest / Vitest | Function-level correctness |
| Integration Tests | pytest | Cross-module correctness |
| SAST | Semgrep + Bandit | Code vulnerabilities |
| SCA | pip-audit / npm audit | Dependency vulnerabilities |
| Secrets | Gitleaks | No leaked credentials |
| Coverage | Coverage.py / Istanbul | Coverage must not decrease |
| Build | Vite / Docker | Successful build |

**If ANY gate fails → PR cannot be merged. No exceptions. No overrides.**

---

## Git Worktrees: Optional Tool

Git worktrees are **NOT required** but are **available as an optional tool** for specific scenarios:

| Scenario | Use Worktree? |
|----------|--------------|
| Normal feature development | ❌ Feature branch is sufficient |
| Hotfix while mid-feature | ✅ Worktree avoids stash/context loss |
| Reviewing someone else's PR locally | ✅ Worktree keeps your work intact |
| Long-running experiment (> 2 days, approved exception) | ✅ Worktree isolates risk |
| Comparing two branches side-by-side | ✅ Worktree enables visual comparison |

### Worktree Quick Reference

```bash
# Create worktree for a hotfix while mid-feature
git worktree add ../merx-hotfix hotfix/auth-fix

# Work in the worktree directory
cd ../merx-hotfix
# ... make changes, commit, push, open PR ...

# Remove worktree when done
git worktree remove ../merx-hotfix
```

---

## Hotfix Protocol (P0 / P1)

```
1. Create hotfix branch: git checkout -b hotfix/description
2. Fix + minimal test
3. Open PR with "HOTFIX" label → expedited review (1 reviewer, 30-min SLA)
4. CI gates still run (no bypass)
5. Merge → auto-deploy to staging → smoke test → production
6. Post-mortem within 48 hours (see 07_CONTINUOUS_IMPROVEMENT)
```

---

## Prohibited Actions

| Action | Why Prohibited | Consequence |
|--------|---------------|-------------|
| Push directly to `main` | Bypasses all validation | Branch protection blocks it (enforced) |
| Force push to `main` | Destroys history | Branch protection blocks it |
| Merge with failing CI | Ships broken code | GitHub blocks it |
| Merge without review | No quality check | GitHub blocks it |
| Long-lived branches (> 3 days) | Merge conflict risk | Flagged in standup, escalated |
| Rewriting published history | Confuses collaborators | `--force-with-lease` only on own branches |

---

## Integration with Ecosystem

| Document | Relationship |
|----------|-------------|
| [02_GOVERNANCE](./02_GOVERNANCE_AND_DECISIONS.md) | Change policy is a T4 squad-level standard |
| [03_COMMUNICATION](./03_COMMUNICATION_MODEL.md) | PR descriptions are async communication |
| [05_ACCOUNTABILITY](./05_ACCOUNTABILITY_SYSTEM.md) | Code review turnaround tracked as metric |
| [07_CONTINUOUS_IMPROVEMENT](./07_CONTINUOUS_IMPROVEMENT.md) | Post-mortems for failed deploys |
| [Head of DevOps](./nodes/L3_HEAD_DEVOPS.md) | Owns CI/CD pipeline enforcement |
| [Head of Security](./nodes/L3_HEAD_SECURITY.md) | Owns security gates |
| [Head of QA](./nodes/L3_HEAD_QA.md) | Owns test coverage gates |
| [Release Committee](./nodes/committees/COMMITTEE_RELEASE.md) | Go/No-Go for production |
