# DevOps Node — Claude Code Instructions

## Scope
Infrastructure, CI/CD, deployments, platform reliability. $0 infra philosophy.

## Source Code
- CI/CD: `.github/workflows/`
- Docker: `Dockerfile`, `Dockerfile.railway`, `docker-compose.yml`
- Nginx: `nginx.conf` (if present)

## Deployment Targets
| Service | Platform | Trigger |
|---------|----------|---------|
| Backend | Railway | push to master |
| Frontend | Vercel | push to master (`frontend/**`) |
| Landing | Vercel | push to master (`landing/**`) |

## Critical Rules
- Vercel deploys use CLI directly (`vercel --prod`) — NOT `amondnet/vercel-action` (broken).
- Railway backend: `--workers 1` (SSEManager in-memory, no multi-worker).
- NEVER push secrets to workflows. Use GitHub Secrets.
- Pre-commit blocks direct push to master. Always use feature branch + PR.

## Key Secrets (GitHub)
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID` (frontend), `VERCEL_PROJECT_ID_LANDING`
- Railway deploy via `RAILWAY_TOKEN`

## Run Commands
```bash
docker-compose up -d              # local dev stack
gh workflow run deploy-frontend   # manual trigger
```

## Agent
`.claude/agents/devops-engineer.md`

## Node Details
`NODE.md` in this directory.
