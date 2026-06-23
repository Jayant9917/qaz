## Personal AI Operating System

Version: 1.0

Owner: Jay Rana

---

# Vision

NOVO is a Personal AI Operating System designed to act as a real-life digital assistant.

Unlike traditional chatbots, NOVO will have:

- Memory
- Reasoning
- Tool Usage
- Voice Interaction
- Personal Knowledge
- Automation Capabilities
- Dashboard Management
- Multi-Model Intelligence

NOVO should evolve into an AI companion capable of understanding the user, managing information, automating work, and assisting with daily life.

---

# Core Philosophy

NOVO is NOT a chatbot.

NOVO is:

Brain

+

Memory

+

Tools

+

Knowledge

+

Voice

+

Automation

---

# Architecture Overview

Frontend

↓

API Gateway

↓

Agent Engine

↓

Memory System

↓

Knowledge System

↓

Tool System

↓

Model Router

↓

OpenRouter

↓

LLMs

---

# Technology Stack

## Frontend

Next.js

TypeScript

TailwindCSS

Shadcn UI

Framer Motion

React Query

---

## Backend

Python

FastAPI

Pydantic

SQLAlchemy

Alembic

---

## Database

PostgreSQL

Stores:

- Users
- Tasks
- Memories
- Conversations
- Analytics
- Tool Logs

---

## Vector Database

Milvus

Stores:

- Embeddings
- Semantic Memories
- Document Chunks
- Conversation Embeddings

---

## Cache Layer

Redis

Stores:

- Sessions
- Agent State
- Recent Chat History
- Frequently Accessed Data

---

## Object Storage

MinIO

Stores:

- PDFs
- Images
- Audio Files
- Screenshots
- Videos

---

## Queue System

RabbitMQ

Handles:

- Embedding Jobs
- PDF Processing
- Voice Processing
- Long Running Tasks

---

## Observability

Langfuse

Tracks:

- Prompt Performance
- Costs
- Failures
- Agent Runs
- Latency

---

## Voice

Speech To Text

- Faster Whisper

Text To Speech

- Piper TTS

---

## Automation

Playwright

PyAutoGUI

Pynput

---

## AI Gateway

OpenRouter

Supported Models:

- GPT
- Claude
- Gemini
- DeepSeek
- Llama
- Qwen

---

# Memory Architecture

## Short Term Memory

Storage:

Redis

Purpose:

Current conversation context

---

## Long Term Memory

Storage:

PostgreSQL

Purpose:

Facts about user

Preferences

Goals

Tasks

Profile Information

---

## Semantic Memory

Storage:

Milvus

Purpose:

Meaning based memory retrieval

---

## Episodic Memory

Storage:

PostgreSQL

Purpose:

Past actions

Past conversations

Tool usage history

Agent runs

---

# Agent System

NOVO should use a custom agent framework.

No LangChain.

No LlamaIndex.

Custom implementation.

Agent Responsibilities:

- Planning
- Tool Selection
- Tool Execution
- Memory Retrieval
- Response Generation
- Multi-step Workflows

---

# Tool Registry

Every tool should be registered dynamically.

Tools:

Weather Tool

Calendar Tool

Reminder Tool

Email Tool

File System Tool

Browser Tool

Search Tool

GitHub Tool

VS Code Tool

Database Tool

Terminal Tool

PDF Tool

Document Search Tool

Task Tool

Notes Tool

---

# Production RAG Architecture

Document Upload

↓

Parser

↓

Cleaner

↓

Metadata Extraction

↓

Semantic Chunking

↓

Embedding Generation

↓

Milvus Storage

↓

Retrieval

↓

Re-ranking

↓

Prompt Builder

↓

Model

↓

Response

---

# RAG Components

## Document Parser

Supported Files:

PDF

DOCX

TXT

Markdown

HTML

---

## Metadata Extraction

Store:

Document Name

Author

Page Number

Created Date

Source

Tags

Section

---

## Chunking

Use Semantic Chunking

Avoid fixed chunking

Chunk based on:

- Headings
- Paragraphs
- Sections
- Semantic Boundaries

---

## Embeddings

Store:

Chunk Text

Metadata

Vector

Document Relationship

---

## Retrieval

Top K Search

Metadata Filtering

Hybrid Search

Semantic Search

---

## Re-ranking

Improve retrieval quality before context generation

---

# Dashboard

Purpose:

Allow complete transparency of NOVO.

---

## Dashboard Modules

### User Profile

Personal Information

Preferences

Goals

---

### Memory Center

What NOVO knows

Why it knows it

Source of memory

Memory editing

Memory deletion

---

### Documents

Uploaded documents

Indexed documents

Embedding status

Retrieval metrics

---

### Agent Runs

Execution history

Success rate

Failures

Token usage

---

### Tool Usage

Tool logs

Tool execution metrics

---

### Analytics

Prompt count

Response count

Cost analysis

Performance metrics

---

### Settings

Model selection

Voice settings

Memory settings

Security settings

---

# Voice Assistant

Features:

Wake Word

Voice Chat

Voice Commands

Task Execution

Tool Usage

Natural Conversation

Future Goal:

Hands-free operation

---

# Model Router

Simple Tasks

→ Gemini Flash

Coding

→ DeepSeek

Reasoning

→ Claude

Large Context

→ Gemini Pro

Premium Mode

→ GPT

Router decides automatically.

---

# Security

Authentication

Authorization

Encrypted Secrets

Rate Limiting

Audit Logs

Session Management

Memory Controls

User Permissions

---

# Future Features

Knowledge Graph

Neo4j

Personal Digital Twin

Multi-Agent Collaboration

Smart Home Integration

Local Models

Offline Mode

Wearable Integration

Mobile Application

Desktop Application

Real-time Screen Understanding

Computer Use Agents

---

# Folder Structure

novo

backend

api

agents

memory

short_term

long_term

semantic

episodic

rag

ingestion

chunking

embeddings

retrieval

reranking

tools

workflows

voice

queues

workers

database

services

observability

models

mcp

frontend

dashboard

docs

infra

docker

scripts

tests

---

# Phase 1

Authentication

Chat Interface

OpenRouter Integration

Conversation Storage

Basic Dashboard

---

# Phase 2

Memory System

Redis

Long-Term Memory

Memory Dashboard

---

# Phase 3

Milvus Integration

Document Upload

Semantic Search

Production RAG

---

# Phase 4

Voice Assistant

Whisper

Piper

Wake Word

---

# Phase 5

Custom Agent Engine

Tool Calling

Multi-step Workflows

Automation

---

# Phase 6

Desktop Automation

Browser Automation

VS Code Integration

Computer Control

---

# Phase 7

Knowledge Graph

Neo4j

Advanced Personal Memory

Digital Twin

---

# Ultimate Goal

Build NOVO into a complete Personal AI Operating System capable of:

- Remembering
- Learning
- Reasoning
- Searching
- Automating
- Communicating
- Assisting

with a transparent dashboard showing exactly what it knows, why it knows it, and how it operates.



# NOVO Security & Governance Layer

## Core Principle

NOVO must never perform sensitive actions without the owner's knowledge, approval, and visibility.

The user must always remain in control.

---

## NOVO Control Center

A dedicated admin dashboard for managing:

- Permissions
- Memory
- Tool Access
- Audit Logs
- Security Policies
- Agent Actions

---

## Permission System

Every tool must have permissions.

States:

- Allow
- Deny
- Ask Every Time

Examples:

Email Tool

- Read Emails
- Send Emails

Browser Tool

- Read Websites
- Submit Forms

Filesystem Tool

- Read Files
- Write Files
- Delete Files

---

## Action Risk Levels

### Level 1 — Safe

No approval required.

Examples:

- Weather
- Search Documents
- Read Notes

### Level 2 — Sensitive

Requires confirmation.

Examples:

- Send Message
- Send Email
- Create Calendar Event

### Level 3 — Critical

Always requires approval.

Examples:

- Delete Files
- Database Modifications
- Financial Actions

---

## Privacy Firewall

All requests pass through a privacy layer before reaching any LLM.

Responsibilities:

- Remove secrets
- Remove credentials
- Redact sensitive information
- Enforce memory permissions

---

## Memory Classification

Every memory has a security level.

Public

Private

Confidential

Secret

Restricted

The LLM can only access memories permitted by policy.

---

## Human Approval Engine

Required for:

- Messaging
- Email Sending
- Calendar Changes
- File Deletion
- Data Export
- Social Media Posting

---

## Audit System

Track:

- Tool Calls
- Agent Decisions
- Model Usage
- User Approvals
- Memory Access

Everything must be explainable.

---

## Explainability Engine

NOVO must explain:

- Why a tool was selected
- Why a memory was used
- Why a model was selected
- Why an action was taken

---

## Emergency Kill Switch

Capabilities:

- Stop all agents
- Disable automation
- Revoke sessions
- Disable tool access

Instantly.

---

## Security Modes

Observer Mode

Read Only

Assistant Mode

Suggest Only

Operator Mode

Execute With Approval

Autonomous Mode

Execute Within Approved Policies

Default Mode:

Assistant Mode

---

## Secrets Vault

Store:

- API Keys
- Passwords
- Tokens
- Credentials

Never store secrets inside memory systems.

---

## Zero Trust Principle

Every action must be:

Authenticated

Authorized

Logged

Explainable

Auditable

Revocable