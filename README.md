
# MERX v2


## Instalación de uv

- Windows: https://docs.astral.sh/uv/getting-started/installation/#windows

```powershell

powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

```

- macOS: https://docs.astral.sh/uv/getting-started/installation/#macos

```sh

curl -LsSf https://astral.sh/uv/install.sh | sh

```


# Security Guide — Merx v2 / Chandelier ERP

## Para contribuyentes: configuración inicial (5 minutos)

### 1. Instalar pre-commit (una vez por máquina)
```bash
pip install pre-commit
pre-commit install
```
Desde este momento, cada `git commit` corre automáticamente:
- **Gitleaks** — bloquea el commit si detecta contraseñas o tokens
- **Ruff** — linter Python
- **Bandit** — análisis de seguridad estático
- Higiene básica (espacios, archivos grandes, conflictos de merge)

### 2. Crear tu `.env` local
```bash
cp .env.example .env   # si existe, o pide el .env al maintainer
```
**Nunca** escribas una contraseña real en ningún archivo que no sea `.env`.
El `.env` está en `.gitignore` — nunca se sube a GitHub.

---

## Pruebas de seguridad locales

### SAST — Semgrep (reglas custom de tenant isolation)
```bash
pip install semgrep
semgrep --config=.semgrep/rules/ backend/
```
Verifica que todas las rutas tengan `tenant_id` y sin credenciales hardcodeadas.

### Secrets — Gitleaks
```bash
# Escanear repo completo
gitleaks detect --config=.gitleaks.toml --verbose --redact

# Escanear solo archivos staged antes de commit
gitleaks protect --staged --config=.gitleaks.toml
```

### Dependencias — Python
```bash
pip install safety
safety check -r requirements.txt
```

### Dependencias — Node
```bash
cd frontend && npm audit --audit-level=high
```

### Suite de tests de seguridad
```bash
# Desde la raíz del proyecto
uv run pytest tests/security/ -v
```
Cubre: tenant isolation, auth bypass, rate limiting, SQL injection.

### Imagen Docker
```bash
docker build -f Dockerfile.backend -t chandelier-backend:local .
trivy image chandelier-backend:local --severity CRITICAL,HIGH
```

---

## Qué revisa GitHub en cada PR (automático)

| Workflow | Qué hace | Dónde ver resultados |
|----------|----------|----------------------|
| `sast.yml` | CodeQL + Semgrep | Security tab → Code scanning |
| `secret-scan.yml` | Gitleaks en el diff | Job logs |
| `sca.yml` | `safety` + `npm audit` | Job logs |
| `container-security.yml` | Trivy imagen Docker | Security tab → Code scanning |
| `ai-review.yml` | Claude revisa el diff | Comentario en el PR |
| `dast.yml` | OWASP ZAP (semanal) | Security tab / GitHub Issues |

---

## Reglas que SIEMPRE aplican

- **Nunca** hardcodear contraseñas, tokens o connection strings en código
- **Nunca** hacer commit de archivos `.env*` (excepto `.env.example` sin valores reales)
- Toda ruta de FastAPI que acceda a datos de tenant debe llamar `set_tenant_context_for_session()`
- PRs con hallazgo CRITICAL del AI reviewer son bloqueados automáticamente

## Reporte de vulnerabilidades

Encontraste un bug de seguridad? No abras un issue público.
Envía un email a: **[maintainer email]** con asunto `[SECURITY] descripción breve`.
