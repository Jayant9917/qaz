# NOVO command cheat sheet

## Start the whole dev stack

```powershell
cd D:\NOVO
pnpm dev
```

## Start only one part

Backend only:

```powershell
cd D:\NOVO
pnpm dev:backend
```

Frontend only, through WSL Ubuntu:

```powershell
cd D:\NOVO
pnpm dev:frontend
```

Infrastructure only:

```powershell
cd D:\NOVO
pnpm dev:infra
```

## Run frontend manually in WSL

```bash
cd /mnt/d/NOVO/frontend
NEXT_TELEMETRY_DISABLED=1 pnpm dev
```

## Run backend manually in Windows

```powershell
cd D:\NOVO\backend
python -m uvicorn novo.main:app --reload --app-dir src --host 127.0.0.1 --port 8000
```

## Build and verify

Frontend build in WSL:

```bash
cd /mnt/d/NOVO/frontend
NEXT_TELEMETRY_DISABLED=1 pnpm run build
```

Frontend lint and typecheck:

```powershell
cd D:\NOVO\frontend
pnpm lint
pnpm typecheck
```

Backend tests:

```powershell
cd D:\NOVO\backend
python -m pytest
```

Database migration:

```powershell
cd D:\NOVO\backend
python -m alembic upgrade head
```

## Stop dev processes

Use `Ctrl+C` in the terminal that started `pnpm dev`, `pnpm dev:backend`, or `pnpm dev:frontend`.
