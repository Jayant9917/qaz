# NOVO Scripts

Small developer entry points for NOVO.

## Dev launcher

- `pnpm dev` starts infrastructure, backend, and frontend together after reclaiming ports 3000 and 8000 if they are already in use.
- `pnpm dev:backend` starts only the backend API in the current terminal after reclaiming port 8000.
- `pnpm dev:frontend` starts only the frontend app inside WSL Ubuntu after reclaiming port 3000 so Next.js can build and reload cleanly on this machine.
- `pnpm dev:infra` starts only the Docker infrastructure.
- `pnpm ports:free` stops whatever is already listening on ports 3000 and 8000.

The launcher keeps logs visible in the terminal, and `Ctrl+C` stops the running dev processes cleanly.
