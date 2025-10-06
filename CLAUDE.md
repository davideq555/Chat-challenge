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
├── uploads/                 # Uploaded files (images, documents)
│   └── .gitkeep             # Keep directory in git
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── venv/                    # Virtual environment
```

### Data Model Relationships

- **Users** - Can create messages and participate in chat rooms
- **ChatRooms** - Can be 1-to-1 or group chats, contain messages
- **RoomParticipants** - Many-to-many relationship between Users and ChatRooms (SECURITY)
- **Messages** - Belong to a room and user, can have attachments, support soft delete
  - Relationship: `Message.attachments` → `List[Attachment]` (lazy="joined")
- **Attachments** - Belong to messages, store file URLs and types
  - Relationship: `Attachment.message` → `Message` (back_populates="attachments")

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
   - JWT authentication via `get_current_user` dependency
   - Returns 403 Forbidden if user is not a participant

7. **File Upload System**:
   - Files stored locally in `/uploads/` directory
   - Hashed filenames: `{timestamp}_{sha256hash}_{uuid}.{ext}`
   - Prevents name collisions and exposes file structure
   - Served as static files via FastAPI `StaticFiles` mount
   - Flow: Upload file → Get URL → Create message with attachment
   - Maximum file size: 10MB
   - Allowed types: images (jpg, png, gif, webp), documents (pdf, doc, docx)

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
- `POST /chat-rooms/` - Create room (requires JWT, creator auto-added as participant)
- `GET /chat-rooms/` - List ALL rooms (admin endpoint - consider restricting)
- `GET /chat-rooms/my-rooms` - Get rooms where authenticated user is participant (SECURE)
- `GET /chat-rooms/{room_id}` - Get room (validates participation via JWT)
- `PUT /chat-rooms/{room_id}` - Update room (validates participation via JWT)
- `DELETE /chat-rooms/{room_id}` - Delete room (requires JWT, validates participation)
  - Cascade deletion: attachments → messages → participants → chat_room
  - Ensures no orphaned data or foreign key violations

### Room Participants (`/chat-rooms/{room_id}/participants`)
- `POST /chat-rooms/{room_id}/participants?user_id={id}` - Add participant
- `DELETE /chat-rooms/{room_id}/participants/{user_id}` - Remove participant
- `GET /chat-rooms/{room_id}/participants` - List participants

### Messages (`/messages`) - WITH SECURITY VALIDATION
- `POST /messages/` - Create message (requires JWT, validates user is participant)
  - Accepts optional `attachments[]` array with `{file_url, file_type}`
  - Creates message and attachments in single transaction using `db.flush()`
  - Response includes message with populated attachments array
- `GET /messages/` - List messages (requires JWT, filter by room_id, user_id)
- `GET /messages/{message_id}` - Get message (requires JWT, validates access)
- `PUT /messages/{message_id}` - Update message content (requires JWT, only author)
  - Broadcasts `message_updated` event via WebSocket
- `DELETE /messages/{message_id}` - Delete message (requires JWT, only author, soft delete by default)
  - Broadcasts `message_deleted` event via WebSocket
- `POST /messages/{message_id}/restore` - Restore soft-deleted message (requires JWT, only author)
- `GET /messages/room/{room_id}/latest` - Get recent messages (requires JWT, validates access, uses cache)

### Attachments (`/attachments`)
- `POST /attachments/upload` - Upload file to server (requires JWT, max 10MB)
  - Accepts: images (jpg, png, gif, webp) and documents (pdf, doc, docx)
  - Returns: `{file_url, file_name, file_type, file_size}`
  - Files saved with hashed names: `{timestamp}_{sha256hash}_{uuid}.{ext}`
  - Stored in `/uploads/` directory, served as static files
- `POST /attachments/` - Create attachment metadata (links file to message)
- `GET /attachments/` - List attachments (filter by `message_id`, `file_type`)
- `GET /attachments/{attachment_id}` - Get attachment
- `PUT /attachments/{attachment_id}` - Update attachment
- `DELETE /attachments/{attachment_id}` - Delete attachment
- `GET /attachments/message/{message_id}/all` - Get all attachments for a message
- `GET /attachments/message/{message_id}/count` - Count attachments
- `GET /attachments/stats/by-type` - Statistics by file type

### WebSockets
- `ws://localhost:8000/ws/{room_id}?token={JWT}` - Real-time messaging
- Supported message types:
  - `message` - New message received
  - `message_updated` - Message edited by author
  - `message_deleted` - Message deleted by author
  - `typing` - User typing indicator
  - `online` / `offline` - User status changes
  - `join_room` / `leave_room` - Room membership events

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
- **JWT Authentication**: Implemented with access tokens
  - Login endpoint returns `{access_token, user}` object
  - Token stored in localStorage on frontend
  - Protected endpoints use `get_current_user` dependency
  - Token passed via `Authorization: Bearer <token>` header
- **Password Hashing**: Currently SHA256 (TODO: upgrade to bcrypt)
- **TODO**: Implement refresh tokens for better security
- **TODO**: Add token expiration and renewal mechanism

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

## Frontend Integration

### Technology Stack
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI component library
- **WebSocket Client** - Real-time communication

### Key Features Implemented

#### 1. File Upload System
- **Flow**: Upload file → Get URL → Send message with attachment
- Files uploaded to `POST /attachments/upload` before message creation
- Frontend constructs full URLs: `http://localhost:8000/uploads/{filename}`
- Supports images and documents (10MB max)
- Preview for images before sending

#### 2. Message Management
- **Edit Messages** (WhatsApp-style):
  - Click "Editar" → Message content loads into chat input
  - Edit bar appears above input with "Cancelar" button
  - Press Enter to save, Escape to cancel
  - Updates via API and broadcasts to other users via WebSocket
- **Delete Messages**:
  - Click "Eliminar" → Custom confirmation modal appears
  - Soft delete by default (can be restored)
  - Broadcasts deletion to other users in real-time
- **Message Bubbles**:
  - Dynamic width based on content (not fixed 70%)
  - Context menu (3 dots) appears on hover for own messages
  - Only text messages can be edited (not attachments)

#### 3. Conversation Management
- **Delete Conversations**:
  - Available in chat header dropdown menu
  - Only enabled for 1-to-1 chats (disabled for group chats)
  - Custom confirmation modal with destructive styling
  - Backend deletes in cascade: attachments → messages → participants → room

#### 4. UI Components
- **ConfirmDialog**: Reusable confirmation modal component
  - Based on shadcn/ui AlertDialog
  - Supports `variant="destructive"` for delete actions
  - Used for both message and chat deletion
- **MessageBubble**: Smart message component
  - Renders text, images, and documents differently
  - Integrates attachments with timestamps
  - Shows sender name in group chats

#### 5. Real-time Sync
- WebSocket handles:
  - `message_updated` - Syncs edits across clients
  - `message_deleted` - Removes messages in real-time
  - Message type properly typed in frontend (`lib/websocket.ts`)

### Configuration
- API base URL: `http://localhost:8000`
- WebSocket URL: `ws://localhost:8000/ws/{room_id}`
- CORS configured to allow all origins: `allow_origins=["*"]`
- JWT token stored in localStorage

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

### Important Implementation Notes

#### Message with Attachments Flow
```python
# Backend (messages.py)
message = Message(...)
db.add(message)
db.flush()  # Get message.id without committing

if message_data.attachments:
    for attachment_data in message_data.attachments:
        attachment = Attachment(message_id=message.id, ...)
        db.add(attachment)

db.commit()  # Commit everything in one transaction
```

#### Cascade Deletion Order
```python
# Delete room (chat_rooms.py)
# 1. Get all messages
messages = db.query(Message).filter(Message.room_id == room_id).all()

# 2. Delete attachments for each message
for message in messages:
    db.query(Attachment).filter(Attachment.message_id == message.id).delete()

# 3. Delete messages
db.query(Message).filter(Message.room_id == room_id).delete()

# 4. Delete participants
db.query(RoomParticipant).filter(RoomParticipant.room_id == room_id).delete()

# 5. Delete room
db.delete(chat_room)
db.commit()
```

#### WebSocket Message Types (Frontend)
```typescript
// lib/websocket.ts
type WebSocketMessage = {
  type: "message" | "typing" | "online" | "offline" |
        "join_room" | "leave_room" | "message_updated" | "message_deleted"
  data?: any
  content?: string
  messageId?: string
}
```

#### File Upload Security
- Max file size: 10MB (enforced in backend)
- Allowed MIME types validated server-side
- Filenames hashed to prevent:
  - Name collisions
  - Path traversal attacks
  - Information leakage about upload order/user
- Files stored outside of code directory (`/uploads/`)
- Consider implementing virus scanning for production

### Completed Features ✅
1. ✅ JWT authentication implemented (bcrypt + access tokens)
2. ✅ File upload for attachments (images and documents, max 10MB)
3. ✅ Static file serving from `/uploads/` directory
4. ✅ Message editing with real-time sync via WebSocket
5. ✅ Message deletion with real-time sync via WebSocket
6. ✅ Cascade deletion for chat rooms (attachments → messages → participants → room)
7. ✅ Frontend implemented with Next.js + TypeScript + Tailwind
8. ✅ Custom UI components (ConfirmDialog, MessageBubble)
9. ✅ WhatsApp-style message editing (edit in chat input)

### Known TODOs
1. Upgrade password hashing from SHA256 to bcrypt
2. Add WebSocket JWT authentication (currently uses query param)
3. Implement rate limiting for API endpoints
4. Add user roles (admin, moderator, user)
5. Implement read receipts for messages
6. Add typing indicators via WebSocket (partially implemented)
7. File upload to cloud storage (S3, Cloudinary) instead of local `/uploads/`
8. Hard delete for attachments when messages are deleted
9. Image compression/resizing before upload
10. Support for more file types (video, audio, etc.)
