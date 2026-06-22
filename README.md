
# FastAPI ChatAPI

🌍 Languages: [🇬🇧 English](README.md) | [🇷🇺 Русский](README.ru.md)

A real-time chat application built with FastAPI, WebSockets, PostgreSQL, Redis, and Celery.

This project demonstrates how to combine REST APIs, JWT authentication, WebSocket communication, background task processing, file sharing, and image processing into a modern chat backend.


## Features

### Authentication
- User registration
- Password hashing with bcrypt
- JWT-based authentication
- Protected routes

### User Profiles
- View and update profile information
- Avatar uploads
- Automatic avatar resizing with Celery + Pillow
- Cached profile responses

### Rooms
- Create public and private chat rooms
- Join and leave rooms
- View room members
- Browse public rooms

### Messaging
- Real-time messaging with WebSockets
- Message history retrieval
- Cursor-based pagination
- Typing indicators
- Presence notifications
- Online user tracking

### File Sharing
- Upload files to rooms
- Image thumbnail generation
- Real-time file sharing notifications

### Background Tasks
- Redis-backed Celery workers
- Avatar processing
- Thumbnail generation
- Scheduled message delivery (WIP)


## Tech Stack

| Layer | Technology |
|---------|------------|
| API Framework | FastAPI |
| Authentication | JWT (python-jose) |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Database | PostgreSQL |
| Cache | fastapi-cache2 |
| Message Broker | Redis |
| Task Queue | Celery |
| Image Processing | Pillow |
| Real-Time Communication | WebSockets |
| Containerization | Docker Compose |
| Testing | Pytest, HTTPX |


## Architecture

```text
                    ┌─────────────┐
                    │   Client    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 PostgreSQL          Redis Cache      Celery Worker
                                               │
                                               ▼
                                       Image Processing
```

For real-time messaging:

```text
Client A ◄────► FastAPI WebSocket ◄────► Client B
```


# Local Development

## Prerequisites

- Docker
- Docker Compose
- Python 3.12+
- PostgreSQL (if running without Docker)


## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql://chatapp_user:chatapp_pass@db:5432/chatapp
JWT_SECRET=your-secret-key
REDIS_URL=redis://redis:6379/0
UPLOAD_PATH=uploads
```

---

## Running with Docker

Build and start:

```bash
docker compose up --build
```

Subsequent runs:

```bash
docker compose up -d
```

Run migrations:

```bash
docker compose run --rm app uv run alembic upgrade head
```

View worker logs:

```bash
docker compose logs -f worker
```

Restart the Celery worker:

```bash
docker compose restart worker
```

Stop everything:

```bash
docker compose down -v
```


## Database Setup (Without Docker)

### Create Database

```bash
psql -U postgres
```

```sql
CREATE DATABASE chatapp;

CREATE USER chatapp_user WITH PASSWORD 'chatapp_pass';

GRANT ALL PRIVILEGES ON DATABASE chatapp TO chatapp_user;

\q
```

Grant schema permissions:

```bash
psql -U postgres -d chatapp -h localhost
```

```sql
GRANT ALL ON SCHEMA public TO chatapp_user;

\q
```

### Run Migrations

Initialize Alembic:

```bash
alembic init alembic
```

Generate migration:

```bash
alembic revision --autogenerate -m "initial"
```

Apply migration:

```bash
alembic upgrade head
```


# API Overview

## Authentication

### Register

```http
POST /auth/register
```

Creates a new user account.

### Login

```http
POST /auth/login
```

Returns a JWT access token.


## Users

### Get Current User

```http
GET /users/me
```

### Update Profile

```http
PATCH /users/me
```

### Upload Avatar

```http
POST /users/me/avatar
```


## Rooms

### Create Room

```http
POST /rooms
```

### List Public Rooms

```http
GET /rooms
```

### Join Room

```http
POST /rooms/{id}/join
```

### Leave Room

```http
DELETE /rooms/{id}/leave
```

### List Members

```http
GET /rooms/{id}/members
```

---

## Messages

### Get Messages

```http
GET /rooms/{id}/messages
```

Supports cursor pagination:

```http
GET /rooms/{id}/messages?before=123
```


## Files

### Upload File

```http
POST /rooms/{id}/files
```

### List Files

```http
GET /rooms/{id}/files
```


# WebSocket API

Connect:

```text
ws://localhost:8000/ws/rooms/{room_id}?token=<JWT>
```

## Client Events

### Message

```json
{
  "type": "message",
  "content": "Hello world"
}
```

### Typing Indicator

```json
{
  "type": "typing"
}
```

## Server Events

### User Joined

```json
{
  "type": "user_joined",
  "user_id": 1
}
```

### User Left

```json
{
  "type": "user_left",
  "user_id": 1
}
```

### File Shared

```json
{
  "type": "file_shared",
  "file_url": "...",
  "filename": "image.png"
}
```


# Architecture Decisions

## Why FastAPI + Async?

Most chat workloads are I/O-bound rather than CPU-bound.

While users are connected, the server spends most of its time waiting for:

- Incoming messages
- Database responses
- Network events

Async endpoints and WebSockets allow thousands of concurrent connections without blocking worker threads.


## JWT Authentication

Authentication flow:

```text
Register
    ↓
Password Hashing
    ↓
Database Storage
    ↓
Login
    ↓
JWT Token
    ↓
Authenticated Requests
```

Benefits:

- Stateless
- Scalable
- REST-friendly
- Easy WebSocket authentication

---

## Cursor Pagination

Offset pagination:

```sql
OFFSET 50 LIMIT 50
```

does not work well in chat systems because new messages constantly shift page boundaries.

Instead:

```http
GET /messages?before=123
```

anchors pagination to a specific message and prevents duplicates or missing messages.


## WebSockets vs REST

| Feature | REST | WebSocket |
|----------|------|------------|
| Persistent Connection | ❌ | ✅ |
| Server Push | ❌ | ✅ |
| Real-Time Updates | ❌ | ✅ |
| Message Overhead | High | Low |
| Chat Applications | Poor Fit | Ideal |

REST is used for:

- Authentication
- Room management
- History retrieval
- File uploads

WebSockets are used for:

- Live messaging
- Presence notifications
- Typing indicators
- Real-time file sharing


# Celery Background Tasks

### Avatar Processing

After avatar upload:

```python
process_avatar.delay(file_path)
```

The worker:

1. Receives the task from Redis
2. Loads the image
3. Resizes it to 256×256
4. Saves the optimized version

### Thumbnail Generation

When image files are uploaded:

```python
generate_thumbnail.delay(file_path)
```

Thumbnail generation happens asynchronously so uploads remain responsive.


# Testing

Run tests:

```bash
docker compose exec app uv run pytest tests/test_auth.py -v
```

Manual WebSocket testing:

```bash
docker compose exec app uv run python tests/manual_ws_test.py --user 1

docker compose exec app uv run python tests/manual_ws_test.py --user 2
```


# Development Notes

Celery workers load task code into memory during startup.

When task implementations change:

```bash
docker compose restart worker
```

is required so workers reload the updated code.

FastAPI runs with:

```bash
--reload
```

during development, so API changes are automatically picked up.


# Future Improvements

- Scheduled messages
- Message editing
- Message deletion
- Read receipts
- Direct messages
- Push notifications
- Rate limiting
- End-to-end encryption
- Horizontal WebSocket scaling


# License

MIT