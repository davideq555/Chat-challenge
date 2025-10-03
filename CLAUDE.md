# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **real-time chat application** consisting of a FastAPI backend and a Next.js frontend (planned). The backend provides REST APIs and will support WebSocket connections for real-time messaging. Currently using in-memory storage with plans to integrate Redis for caching and user status, and a proper database later.

## Backend Architecture

### Technology Stack
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation and schemas
- **Redis** - Planned for caching recent messages and user online status
- **WebSockets** - Planned for real-time communication

### Project Structure

```
backend/
├── app/
│   ├── main.py           # Application entry point, router registration
│   ├── models/           # Data models (User, ChatRoom, Message, Attachment)
│   ├── schemas/          # Pydantic schemas for request/response validation
│   ├── routers/          # API endpoints organized by resource
│   └── services/         # Business logic (Redis service planned here)
├── venv/                 # Virtual environment
└── requirements.txt
```

### Data Model Relationships

- **Users** - Can create messages and belong to chat rooms
- **ChatRooms** - Can be 1-to-1 or group chats, contain messages
- **Messages** - Belong to a room and user, can have attachments, support soft delete
- **Attachments** - Belong to messages, store file URLs and types

### Key Architectural Patterns

1. **Layered Architecture**:
   - Models (data structure) → Schemas (validation) → Routers (endpoints)
   - Each resource (users, chat_rooms, messages, attachments) follows this pattern

2. **In-Memory Storage**:
   - Currently using dictionaries (`users_db`, `chat_rooms_db`, etc.) in each router
   - Each has a counter for ID generation (`user_id_counter`, etc.)
   - **Important**: Data is lost on restart - this is temporary

3. **Schema Inheritance**:
   - `*Base` - Common fields
   - `*Create` - Fields needed for creation
   - `*Update` - Optional fields for updates
   - `*Response` - What clients receive (excludes sensitive data like password_hash)

4. **Soft Delete Pattern**:
   - Messages use `is_deleted` flag instead of hard deletion
   - Allows message restoration and history preservation

## Development Commands

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

### Running the Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Environment Configuration
Copy `.env.example` to `.env` and configure:
- `REDIS_HOST` - Redis server host (when implemented)
- `REDIS_PORT` - Redis port
- `REDIS_DB` - Redis database number

## API Endpoints

### Users (`/users`)
- `POST /users/` - Create user
- `GET /users/` - List all users
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user
- `POST /users/login` - Authenticate user

### Chat Rooms (`/chat-rooms`)
- `POST /chat-rooms/` - Create room
- `GET /chat-rooms/` - List rooms (filter by `is_group`)
- `GET /chat-rooms/{room_id}` - Get room
- `PUT /chat-rooms/{room_id}` - Update room
- `DELETE /chat-rooms/{room_id}` - Delete room

### Messages (`/messages`)
- `POST /messages/` - Create message
- `GET /messages/` - List messages (filter by `room_id`, `user_id`, `include_deleted`)
- `GET /messages/{message_id}` - Get message
- `PUT /messages/{message_id}` - Update message content
- `DELETE /messages/{message_id}` - Delete message (soft/hard)
- `POST /messages/{message_id}/restore` - Restore soft-deleted message
- `GET /messages/room/{room_id}/latest` - Get recent messages for a room

### Attachments (`/attachments`)
- `POST /attachments/` - Create attachment
- `GET /attachments/` - List attachments (filter by `message_id`, `file_type`)
- `GET /attachments/{attachment_id}` - Get attachment
- `PUT /attachments/{attachment_id}` - Update attachment
- `DELETE /attachments/{attachment_id}` - Delete attachment
- `GET /attachments/message/{message_id}/all` - Get all attachments for a message
- `GET /attachments/message/{message_id}/count` - Count attachments
- `GET /attachments/stats/by-type` - Statistics by file type

## Important Notes for Future Development

### Planned Features
1. **WebSocket Integration** - Real-time messaging (not yet implemented)
2. **Redis Integration** - For caching recent messages and tracking online users
3. **Database Migration** - Replace in-memory storage with PostgreSQL/MySQL
4. **Authentication** - Currently using simple SHA256 hashing; needs JWT tokens and bcrypt
5. **File Upload** - Attachments currently only store URLs, need actual file upload handling

### When Adding New Features

1. **New Resource Pattern**:
   - Create model in `app/models/{resource}.py`
   - Create schemas in `app/schemas/{resource}.py`
   - Create router in `app/routers/{resource}.py`
   - Register router in `app/main.py`
   - Export schemas in `app/schemas/__init__.py`

2. **Authentication Consideration**:
   - Password hashing uses simple SHA256 (see `app/routers/users.py`)
   - Should be replaced with bcrypt before production
   - Future: Add JWT authentication middleware

3. **Foreign Key Validation**:
   - Currently no validation that referenced IDs exist (marked with TODO comments)
   - Must be implemented when moving to a database

### Frontend Integration
- Frontend will be built with Next.js (see `frontend/README.md`)
- CORS is configured to allow all origins (`allow_origins=["*"]`)
- API base URL: `http://localhost:8000`
- WebSocket URL (planned): `ws://localhost:8000/ws`
