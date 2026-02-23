# TEAM.md

## Organogram

### Security Architect
**Goal:** Design and implement comprehensive DevSecOps ecosystem for FastAPI + Postgres + React application with multitenant ERP requirements.
**Skills:** DevSecOps methodologies, security tool integration, multitenant architecture security, risk assessment
**Tasks:** Define security layers, select appropriate tools (CodeQL, Semgrep, OWASP ZAP, etc.), design automation workflows, ensure compliance with multitenant security requirements

### Backend Security Engineer
**Goal:** Implement and maintain security controls for FastAPI and Postgres components.
**Skills:** FastAPI security patterns, SQL injection prevention, API authentication/authorization, database security
**Tasks:** Configure CodeQL rules for SQL injection detection, implement Semgrep custom rules for tenant isolation, ensure proper input validation and authentication flows

### Frontend Security Engineer
**Goal:** Secure React frontend and ensure secure communication with backend.
**Skills:** React security best practices, XSS prevention, CORS configuration, client-side security
**Tasks:** Implement ESLint security rules, configure secure headers, validate frontend security flows, integrate with DAST tools

### DevSecOps Engineer
**Goal:** Automate security scanning and protection across the entire CI/CD pipeline.
**Skills:** GitHub Actions, container security, dependency management, automation scripting
**Tasks:** Configure automated scans (CodeQL, Dependabot, Trivy), set up OWASP ZAP in CI/CD, implement container security checks, manage security tooling integration

### Security Automation Specialist
**Goal:** Integrate AI-powered security analysis and custom rule engines.
**Skills:** AI/ML security tools, custom rule engine development, Claude/GPT integration, security pattern recognition
**Tasks:** Configure Claude/GPT code reviewer, develop custom security rules for multitenant patterns, integrate A.C.O.S. Engine, implement automated security decision making

### QA Security Tester
**Goal:** Validate security controls and perform security testing on multitenant features.
**Skills:** Security testing methodologies, penetration testing, multitenant data isolation testing
**Tasks:** Execute OWASP ZAP scans, validate tenant data isolation, perform security regression testing, verify logging and audit trails