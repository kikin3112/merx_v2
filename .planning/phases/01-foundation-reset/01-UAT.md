# Phase 1 UAT: Foundation & Reset

**Objective:** Superadmin can reset database safely and system can generate Excel templates for imports.

| Test ID | Description | Status | Evidence | Notes | Fix |
|---|---|---|---|---|---|
| 1.01 | Application container starts successfully and is healthy. | PASSED | User log | The application container was failing to respond to health checks correctly, returning a `400 Bad Request`. | The `ALLOWED_HOSTS` setting in `config.py` was too restrictive for the Railway environment. The fix involves allowing all hosts (`*`) and re-enabling the `TrustedHostMiddleware` to use this new configuration. This is a temporary measure and should be reviewed before production. |
| 1.02 | Superadmin can execute database reset. | FAILED | Code review | The feature is not implemented. There is no endpoint or script available to perform a database reset. | A new script, `backend/app/utils/reset_db.py`, needs to be created. This script will be responsible for clearing development data while preserving the schema and essential system tables (like `usuarios` for the superadmin, `puc`, `planes`). |
| 1.03 | Database integrity is validated before and after reset. | BLOCKED | | Depends on 1.02. | |
| 1.04 | Audit trail of reset operations is logged. | BLOCKED | | Depends on 1.02. | |
| 1.05 | User can download Excel templates for products, clients, and inventory. | PENDING | | | |
| 1.06 | Backend can parse .xlsx and .csv files. | PENDING | | | |
