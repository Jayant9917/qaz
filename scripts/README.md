# NOVO Scripts

Small developer entry points for NOVO.

## Dev launcher

- `pnpm dev` starts infrastructure, backend, and frontend together.
- `pnpm dev:backend` starts only the backend API in the current terminal.
- `pnpm dev:frontend` starts only the frontend app inside WSL Ubuntu so Next.js can build and reload cleanly on this machine.
- `pnpm dev:infra` starts only the Docker infrastructure.

The launcher keeps logs visible in the terminal, and `Ctrl+C` stops the running dev processes cleanly.
