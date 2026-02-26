# Chandelier - Linter

Ejecuta herramientas de calidad de código Python del proyecto.

## Uso

```
/lint
```

## Comandos

```bash
# Formatear con Black
uv run black backend/

# Ordenar imports
uv run isort backend/

# Linting con flake8
uv run flake8 backend/app/

# Type checking con mypy
uv run mypy backend/app/

# Todo junto (formatear + lint)
uv run black backend/ && uv run isort backend/ && uv run flake8 backend/app/

# Solo archivos cambiados (git)
uv run black $(git diff --name-only --diff-filter=ACMR | grep '\.py$')
uv run flake8 $(git diff --name-only --diff-filter=ACMR | grep '\.py$')
```

## Configuración

El proyecto usa estas configuraciones en `pyproject.toml`:

```toml
[tool.black]
line-length = 88

[tool.isort]
profile = "black"

[tool.flake8]
max-line-length = 88
exclude = .git,__pycache__,venv,alembic
ignore = E203,W503
```
