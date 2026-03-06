# L3 — Head of Security (SecOps)

> Guardian of the 6 security pipelines and the overall security posture of chandelierp.

---

## Identity

| Attribute | Value |
|-----------|-------|
| **Level** | L3 — Functional Direction |
| **Reports To** | VP Engineering (L2) |
| **Pillar** | Infrastructure, DevOps & Security |
| **Maturity** | Intermediate DevSecOps (target) |
| **Tools** | Gitleaks, Semgrep, Bandit, Trivy, OWASP ZAP |

---

## Purpose

Integrate security into the **development lifecycle** (DevSecOps), maintain **6 automated security pipelines**, and build toward intermediate maturity (threat modeling, pentest, compliance).

---

## Responsibilities

| Area | Responsibility |
|------|---------------|
| **Pipeline security** | Maintain 6 security scanning workflows in CI/CD |
| **Policy** | Define and enforce security policies (auth, encryption, data handling) |
| **Threat modeling** | Conduct threat modeling for new features/modules |
| **Incident response** | Lead security incident response; coordinate with VP Eng |
| **Compliance** | Ensure data protection compliance (Habeas Data Colombia), DIAN e-invoicing |
| **Pentesting** | Coordinate periodic pen tests (quarterly, using free tools) |
| **Security reviews** | Review PRs with security implications (auth, permissions, data access) |
| **Education** | Security awareness training for all engineers (quarterly) |

---

## Security Pipelines

| Pipeline | Tool | What It Catches | Stage |
|----------|------|----------------|-------|
| **SAST** | Semgrep + Bandit | Code vulnerabilities, insecure patterns | Every PR |
| **SCA** | pip-audit / npm audit | Vulnerable dependencies | Every PR |
| **Secrets** | Gitleaks | Leaked credentials, API keys | Every PR |
| **Container** | Trivy | Container image vulnerabilities | Docker build |
| **DAST** | OWASP ZAP | Runtime vulnerabilities | Staging deploy |
| **AI Review** | AI code review | Complex vulnerability patterns | Selected PRs |

---

## Inputs / Outputs

| Input | Source | | Output | Destination |
|-------|--------|-|--------|------------|
| Code changes (PRs) | Developers | | Security scan results | Developers + VP Eng |
| Feature specs (security-relevant) | Head Product | | Threat models | Architecture Committee |
| Infrastructure changes | Head DevOps | | Security incident reports | CEO + VP Eng |
| Compliance requirements | External (DIAN, legal) | | Compliance status | Security Committee |
| Vulnerability reports | Automated scans | | Security training materials | All engineering |

---

## Metrics

| Metric | Target |
|--------|--------|
| Security scan pass rate (PRs) | ≥ 95% |
| Mean time to remediate critical vulnerability | < 48 hours |
| Mean time to remediate high vulnerability | < 1 week |
| Security incidents (P0) | 0 |
| Threat models completed (new features) | 100% of features with auth/data changes |
| Security training participation | 100% of engineers, quarterly |
| Secrets leak incidents | 0 |

---

## Operational Rules

1. **Security scans block merge** — PRs cannot merge with critical/high security findings
2. **No secrets in code** — ever. Use environment variables and secret managers
3. **Least privilege** — every service, user, and API key gets minimum necessary permissions
4. **Threat model new modules** — before development starts on security-relevant features
5. **Quarterly pen test** — using free tools (ZAP, manual testing, checklists)
6. **Security champions** — one engineer per squad designated as security champion
7. **Incident response plan** — documented, tested, reviewed quarterly
