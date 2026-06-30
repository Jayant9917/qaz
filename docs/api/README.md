# NOVO API Documentation

This folder documents the NOVO backend API in a way that is easy to scan, easy to extend, and safe to hand off.

## What this folder is for

Use this documentation when you need to understand:

- how NOVO's HTTP API is structured
- which endpoints are available
- which endpoints require authentication or CSRF protection
- what each endpoint does
- how the conversation stream works
- what errors to expect

## API base path

All versioned API routes are served under:

- `/api/v1`

Health endpoints are included in the same API router and are reachable under the same prefix in the running application.

## Quick entry points

Start here:

- [API reference](./API_REFERENCE.md)

Then review the backend source if you need implementation details:

- `D:\NOVO\backend\src\novo\api\v1\router.py`
- `D:\NOVO\backend\src\novo\main.py`
- `D:\NOVO\backend\src\novo\core\config.py`

## Design principles

- Keep the contract explicit.
- Treat authentication and CSRF as first-class requirements for write actions.
- Keep request and response models predictable.
- Prefer stable versioned routes over ad hoc endpoints.
- Document behavior, not just the route path.
