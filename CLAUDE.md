# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **real-time chat application** built as a technical exam for a Full Stack Developer position. The project implements authentication, contact management, persistent messaging with **FastAPI + PostgreSQL + Redis**, and a modern interface in **Next.js**. Additionally includes **file sending**, **security best practices**, and **query optimization**. Execution is orchestrated through **Docker Compose** for simplified deployment.

## Backend Architecture

### Technology Stack
- **FastAPI** - Web framework (Python 3.12)
- **Uvicorn** - ASGI server
- **PostgreSQL** - Main database
- **SQLAlchemy** - ORM with Alembic for migrations
- **Redis** - Cache for recent messages and online user status
- **Pydantic** - Data validation and schemas
- **WebSockets** - Real-time communication (implemented)
- **pytest** - Testing framework

### Project Structure

```
backend/
├── app/
│   ├── main.py              # Application entry point, router registration
│   ├── database.py          # SQLAlchemy engine and session configuration
│   ├── redis_client.py      # Redis client configuration
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── chat_room.py     # ChatRoom model
│   │   ├── message.py       # Message model
│   │   ├── attachment.py    # Attachment model
│   │   └── room_participant.py  # RoomParticipant (many-to-many users-rooms)
│   ├── schemas/             # Pydantic schemas for validation
│   │   ├── user.py
│   │   ├── chat_room.py
│   │   ├── message.py
│   │   ├── attachment.py
│   │   └── room_participant.py
│   ├── routers/             # API endpoints by resource
│   │   ├── users.py
│   │   ├── chat_rooms.py
│   │   ├── messages.py
│   │   └── attachments.py
│   ├── services/            # Business logic
│   │   ├── init_data.py     # Initialize default data (bot, test user, welcome room)
│   │   ├── message_cache.py # Redis cache for messages
│   │   └── user_online.py   # Track online users in Redis
│   └── websockets/          # WebSocket handlers
│       └── manager.py       # WebSocket connection manager
├── tests/                   # Test suite (81 tests)
│   ├── conftest.py          # Test fixtures and setup
│   ├── test_users.py
│   ├── test_chat_rooms.py
│   ├── test_messages.py
│   └── test_attachments.py
├── alembic/                 # Database migrations
│   └── versions/
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── venv/                    # Virtual environment
```

### Data Model Relationships

- **Users** - Can create messages and participate in chat rooms
- **ChatRooms** - Can be 1-to-1 or group chats, contain messages
- **RoomParticipants** - Many-to-many relationship between Users and ChatRooms (SECURITY)
- **Messages** - Belong to a room and user, can have attachments, support soft delete
- **Attachments** - Belong to messages, store file URLs and types

### Key Architectural Patterns

1. **Layered Architecture**:
   - Models (SQLAlchemy) → Schemas (Pydantic) → Routers (FastAPI) → Services (Business Logic)
   - Each resource follows this pattern consistently

2. **PostgreSQL Database**:
   - All data persisted in PostgreSQL
   - SQLAlchemy ORM for database operations
   - Alembic for database migrations
   - Foreign key constraints enforced at DB level

3. **Redis Caching**:
   - Recent messages cached per room (configurable limit)
   - Online users tracked with Sets
   - User connections tracked (multi-device support)
   - Cache invalidation on message creation

4. **Schema Inheritance**:
   - `*Base` - Common fields
   - `*Create` - Fields needed for creation
   - `*Update` - Optional fields for updates
   - `*Response` - What clients receive (excludes sensitive data like password_hash)

5. **Soft Delete Pattern**:
   - Messages use `is_deleted` flag instead of hard deletion
   - Allows message restoration and history preservation

6. **Security Model** (IMPORTANT):
   - **RoomParticipant** model controls access to rooms
   - Users must be participants to access room data
   - All room/message endpoints validate user participation
   - `requesting_user_id` or `user_id` required in sensitive endpoints
   - Returns 403 Forbidden if user is not a participant

## Development Commands

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Linux/Mac
pip install -r requirements.txt
```

### Environment Configuration
Create `.env` file in `backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/db_chat_challenge
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=db_chat_challenge

# SQLAlchemy Configuration
DB_ECHO=false  # Set to true for SQL query debugging

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Database Migrations
```bash
# Create a new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Running the Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
cd backend
pytest -v                    # All tests
pytest tests/test_chat_rooms.py -v   # Specific file
pytest -k "participant" -v   # Tests matching keyword
```

### API Documentation
Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Users (`/users`)
- `POST /users/` - Create user
- `GET /users/` - List all users
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user
- `POST /users/login` - Authenticate user (SHA256 - needs JWT upgrade)

### Chat Rooms (`/chat-rooms`) - WITH SECURITY VALIDATION
- `POST /chat-rooms/?creator_id={id}` - Create room (creator auto-added as participant)
- `GET /chat-rooms/` - List ALL rooms (admin endpoint - consider restricting)
- `GET /chat-rooms/my-rooms/{user_id}` - Get rooms where user is participant (SECURE)
- `GET /chat-rooms/{room_id}?user_id={id}` - Get room (validates participation)
- `PUT /chat-rooms/{room_id}?user_id={id}` - Update room (validates participation)
- `DELETE /chat-rooms/{room_id}?user_id={id}` - Delete room (validates participation)

### Room Participants (`/chat-rooms/{room_id}/participants`)
- `POST /chat-rooms/{room_id}/participants?user_id={id}` - Add participant
- `DELETE /chat-rooms/{room_id}/participants/{user_id}` - Remove participant
- `GET /chat-rooms/{room_id}/participants` - List participants

### Messages (`/messages`) - WITH SECURITY VALIDATION
- `POST /messages/` - Create message (validates user is participant of room)
- `GET /messages/?requesting_user_id={id}&room_id={id}` - List messages (validates access)
- `GET /messages/{message_id}?requesting_user_id={id}` - Get message (validates access)
- `PUT /messages/{message_id}?requesting_user_id={id}` - Update message (only author)
- `DELETE /messages/{message_id}?requesting_user_id={id}` - Delete message (only author, soft/hard)
- `POST /messages/{message_id}/restore?requesting_user_id={id}` - Restore deleted message (only author)
- `GET /messages/room/{room_id}/latest?requesting_user_id={id}` - Get recent messages (validates access, uses cache)

### Attachments (`/attachments`)
- `POST /attachments/` - Create attachment
- `GET /attachments/` - List attachments (filter by `message_id`, `file_type`)
- `GET /attachments/{attachment_id}` - Get attachment
- `PUT /attachments/{attachment_id}` - Update attachment
- `DELETE /attachments/{attachment_id}` - Delete attachment
- `GET /attachments/message/{message_id}/all` - Get all attachments for a message
- `GET /attachments/message/{message_id}/count` - Count attachments
- `GET /attachments/stats/by-type` - Statistics by file type

### WebSockets
- `ws://localhost:8000/ws/{room_id}?token={JWT}` - Real-time messaging (planned JWT auth)

## Security Features

### Access Control
1. **Room Participants Model**:
   - Many-to-many relationship between users and chat rooms
   - Unique constraint on (room_id, user_id) prevents duplicates
   - Cascade delete when room or user is deleted

2. **Endpoint Validation**:
   - All room endpoints validate user is a participant before allowing access
   - Message endpoints validate user is participant of the message's room
   - Update/delete operations validate user is the author (for messages)
   - Returns 403 Forbidden if access denied
   - Returns 404 Not Found if resource doesn't exist

3. **Automatic Participant Addition**:
   - When creating a room, creator is automatically added as participant
   - Ensures creator always has access to their created rooms

### Authentication
- **Current**: SHA256 password hashing (simple implementation)
- **TODO**: Upgrade to bcrypt + JWT tokens for production
- **TODO**: Add JWT middleware for all protected endpoints
- **TODO**: Implement refresh tokens

## Database Schema

### Core Tables
```sql
users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(256) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE
)

chat_rooms (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  is_group BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
)

room_participants (
  id SERIAL PRIMARY KEY,
  room_id INTEGER REFERENCES chat_rooms(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  joined_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(room_id, user_id)
)

messages (
  id SERIAL PRIMARY KEY,
  room_id INTEGER REFERENCES chat_rooms(id),
  user_id INTEGER REFERENCES users(id),
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP,
  is_deleted BOOLEAN DEFAULT FALSE
)

attachments (
  id SERIAL PRIMARY KEY,
  message_id INTEGER REFERENCES messages(id),
  file_url VARCHAR(500) NOT NULL,
  file_name VARCHAR(255),
  file_type VARCHAR(50),
  file_size INTEGER,
  uploaded_at TIMESTAMP DEFAULT NOW()
)
```

## Testing

### Test Coverage
- **81 tests total** (all passing)
- **Users**: 14 tests
- **Chat Rooms**: 25 tests (including security validation)
- **Messages**: 20 tests (including security validation)
- **Attachments**: 22 tests

### Test Structure
- Uses pytest with SQLite in-memory database
- Redis cache cleared before each test
- Fixtures for test client and database session
- Tests include positive and negative cases (403, 404 errors)

### Key Test Patterns
```python
# Creating test data
def test_example(client, db_session):
    # Create user
    user_response = client.post("/users/", json={...})
    user_id = user_response.json()["id"]

    # Create room (user auto-added as participant)
    room_response = client.post(f"/chat-rooms/?creator_id={user_id}", json={...})
    room_id = room_response.json()["id"]

    # Test with validation
    response = client.get(f"/chat-rooms/{room_id}?user_id={user_id}")
    assert response.status_code == 200
```

## Redis Integration

### Message Cache
- Cache recent messages per room (default: 50 messages)
- Ordered set (ZSET) sorted by timestamp
- Cache invalidation on new message
- Fallback to database if cache miss

### Online Users
- Track online users with Redis Sets
- Support multi-device connections per user
- Automatic cleanup on disconnect
- Query methods: `is_user_online()`, `get_online_users()`, `get_online_count()`

## Default Data

On startup, the application initializes:
1. **WelcomeBot** user (ID: varies)
2. **TestUser** (username: TestUser, password: pass1234)
3. **Bienvenida** room (group chat)
4. Both users added as participants to welcome room

## Docker Deployment

```bash
# Start all services
docker-compose up --build

# Services:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000 (planned)
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

## Frontend Integration (Planned)
- Frontend will be built with Next.js
- CORS is configured to allow all origins (`allow_origins=["*"]`)
- API base URL: `http://localhost:8000`
- WebSocket URL: `ws://localhost:8000/ws/{room_id}`

## Important Notes for Development

### When Adding New Features

1. **New Resource Pattern**:
   - Create model in `app/models/{resource}.py`
   - Create schemas in `app/schemas/{resource}.py`
   - Create router in `app/routers/{resource}.py`
   - Register router in `app/main.py`
   - Export schemas in `app/schemas/__init__.py`
   - Create migration: `alembic revision --autogenerate -m "add {resource}"`
   - Write tests in `tests/test_{resource}.py`

2. **Security Checklist**:
   - Add user_id/requesting_user_id parameter to sensitive endpoints
   - Validate user has permission to access resource
   - Return 403 if unauthorized, 404 if not found
   - Test both authorized and unauthorized access
   - Consider if endpoint needs to be in RoomParticipants

3. **Database Changes**:
   - Always create migration with Alembic
   - Test migration upgrade and downgrade
   - Update models and schemas together
   - Run tests after migration

4. **Code Quality**:
   - Set `DB_ECHO=false` in .env to reduce logging
   - Use type hints for all functions
   - Write docstrings for endpoints
   - Follow existing patterns (see other routers)
   - Clean up Redis cache in tests

### Known TODOs
1. Upgrade to JWT authentication (bcrypt + tokens)
2. Implement file upload for attachments
3. Add WebSocket JWT authentication
4. Implement rate limiting
5. Add user roles (admin, moderator, user)
6. Implement read receipts for messages
7. Add typing indicators via WebSocket
8. Frontend development with Next.js
