# Agent Design Research Notes

**Status:** Active research notebook
**Normative specification:** docs/capabilities/07_AGENT_ARCHITECTURE.md

## Purpose

Capture experiments, alternatives, benchmarks, and unresolved questions without changing the accepted Agent Architecture.

## Research topics

- Deterministic versus model request classification
- Planner schema and validation
- Fast-to-Deep escalation quality
- Checkpoint granularity
- Loop/no-progress detection
- Compensation patterns
- Tier 1 versus Tier 2 planning quality
- Worker lease and cancellation behavior
- Multi-agent value and risk

## Experiment template

- Question
- Hypothesis
- Dataset/scenario
- Implementation/version
- Metrics
- Result
- Security impact
- Operational impact
- Recommendation
- Architecture decision required

## Current constraints

No experiment may bypass Guardrails, approval, audit, budgets, or the rule that model output cannot directly execute tools.

====================================

python -m alembic upgrade head is the command that applies all pending database migrations.
In plain English:
Alembic = the tool that manages database schema changes over time
upgrade = apply migrations
head = move the database to the latest version in your project
So when you run that command, NOVO tells PostgreSQL:
create the tables
add the columns
add the indexes
add the relationships
bring the database up to the latest schema the code expects
Why this matters:
your code can change over time, and the database needs a controlled way to change with it. Alembic gives you that controlled history.
What is SQLAlchemy?
SQLAlchemy is the Python library NOVO uses to work with the database.
It does two main jobs:
ORM part
lets you define tables as Python classes
lets you query/update rows using Python objects instead of raw SQL

Core/SQL part
lets you build SQL statements more safely and flexibly

So instead of writing a lot of raw SQL everywhere, you can do things in Python like:
define User, Session, Permission, AuditLog
query them with Python code
let SQLAlchemy generate the actual SQL
How they work together in NOVO
SQLAlchemy defines the models/tables
Alembic tracks changes to those models over time
alembic upgrade head applies those changes to the real database
Simple analogy:
SQLAlchemy = the blueprint and builder
Alembic = the renovation planner and migration history
PostgreSQL = the actual building
If you want, I can also explain:
the difference between ORM and raw SQL
what a migration file looks like
how NOVO’s current 0001_e0 and 0002_e1_auth migrations work step by step