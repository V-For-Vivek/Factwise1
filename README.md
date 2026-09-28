# Team Project Planner

A robust, modular Team Project Planner tool built with **Django** and Python. It implements comprehensive business logic for managing **Users**, **Teams**, and **Project Boards & Tasks**, adhering strictly to the specifications defined in `ProblemStatement.md` and extending the provided abstract base classes (`UserBase`, `TeamBase`, `ProjectBoardBase`).

---

## 1. Project Overview & Architecture

```
                                  Architecture Overview

   +-------------------------------------------------------------------------------+
   |                                 Entry Points                                  |
   |   - Python Concrete Classes: User(UserBase), Team(TeamBase), ProjectBoard(...) |
   |   - Django REST API Endpoints: /api/users/, /api/teams/, /api/boards/         |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                                Django Layer                                   |
   |   - Models: UserModel, TeamModel, BoardModel, TaskModel                       |
   |   - Validation & Business Logic: Uniqueness, Caps, Status Transitions         |
   |   - Board Export Engine: Visual ASCII Kanban Generation (`out/`)              |
   +---------------------------------------+---------------------------------------+
                                           |
                                           v
   +-------------------------------------------------------------------------------+
   |                        Local File Persistence Layer                           |
   |   - Location: db/db.sqlite3 (Isolated within `db/` directory)                |
   |   - Auto-Migration: Automatic schema initialization on first import           |
   +-------------------------------------------------------------------------------+
```

### Key Components

- **Concrete Implementations**:
  - `user.py`: Implements `User` subclassing `UserBase`.
  - `team.py`: Implements `Team` subclassing `TeamBase`.
  - `project_board.py`: Implements `ProjectBoard` subclassing `ProjectBoardBase`.
  - `main.py` / `planner.py` / `__init__.py`: Re-exports `User`, `Team`, `ProjectBoard` for seamless import flexibility.
- **Django Application (`planner/`)**:
  - `models.py`: Schema definitions (`UserModel`, `TeamModel`, `BoardModel`, `TaskModel`) with database-level constraints.
  - `views.py` & `urls.py`: HTTP endpoints under `/api/` exposing all planner capabilities over REST.
  - `tests.py`: 27 comprehensive Django test cases validating all use cases, edge cases, and constraints.
- **Persistence Layer (`db/`)**:
  - Uses SQLite stored at `db/db.sqlite3`.
  - Consumers interact exclusively through APIs; the internal database file is never exposed.
- **Export Engine (`out/`)**:
  - Generates presentation-grade ASCII Kanban reports in `out/board_<id>.txt`.

---

## 2. Thought Process & Design Decisions

### A. Persistence & Encapsulation

- **Choice**: Django ORM with SQLite backend configured to `BASE_DIR / 'db' / 'db.sqlite3'`.
- **Rationale**: Meets the requirement that _"The application should use the local file storage for persistence"_ and _"The db folder should contain all the files created to persist the application data"_. SQLite provides ACID transactions, relational integrity, unique indexing, and zero external service overhead while residing completely within the local `db/` folder.

### B. Zero-Configuration Auto-Initialization

- **Choice**: `init_django.py` hook automatically configures Django settings and applies migrations if the database file or tables are absent.
- **Rationale**: When submitting a project archive, `db/` files are omitted per submission guidelines. Grading scripts or external callers importing `from user import User` will run instantly out-of-the-box without requiring manual `python manage.py migrate` execution.

### C. Creative Board Export (`out/`)

- **Choice**: Detailed text Kanban board featuring:
  - Header with board metadata, team details, and admin information.
  - Dynamic progress bar (`[████████░░░░]`) with completion percentages.
  - Categorized task columns (`[OPEN]`, `[IN PROGRESS]`, `[COMPLETE]`) with assignees and timestamps.
- **Rationale**: Fulfills the requirement to be creative and present a readable, production-grade view of board progress.

---

## 3. Assumptions & Rationale

1. **`describe_user` Output**:
   - _Docstring_: Specifies keys `"name"`, `"description"`, `"creation_time"`.
   - _Assumption_: The user's `display_name` is mapped to `"description"`, aligning with user creation fields while maintaining strict compliance with the output JSON schema.
2. **`add_task` Board Identifier**:
   - _Docstring_: Example payload omitted `board_id`.
   - _Assumption_: The implementation supports `"board_id"` or `"id"` in the request payload. As a fallback, if omitted, the tool automatically resolves the open board belonging to the assigned user's team if a single open board exists; otherwise, a clear `ValueError` is raised.
3. **Team Membership & Constraints**:
   - _Admin Membership_: When a team is created, the specified admin is automatically enrolled as an initial team member.
   - _50-User Cap_: Enforced both as a per-request batch limit (`len(users) <= 50`) and as an absolute team capacity cap (`total_members <= 50`).
4. **Void Return Methods**:
   - _Docstrings_: Methods like `update_user`, `update_team`, `add_users_to_team`, `remove_users_from_team`, `close_board`, and `update_task_status` have empty `:return:` specifications.
   - _Assumption_: Following standard Python idiom (e.g., `dict.update`, `list.append`), these mutating methods return `None` on success and raise descriptive `ValueError` exceptions upon constraint violations.
5. **Timestamp Representation**:
   - Standard ISO `%Y-%m-%d %H:%M:%S` format is used across all responses and board exports.

---

## 4. API Reference & Constraints

| API Method               | Target | Key Constraints & Validations                                                            | Return Format                                                             |
| ------------------------ | ------ | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `create_user`            | User   | Unique name, max 64 chars; display name max 64 chars                                     | `{"id": "<user_id>"}`                                                     |
| `list_users`             | User   | Lists all registered users                                                               | `[{"name": ..., "display_name": ..., "creation_time": ...}]`              |
| `describe_user`          | User   | Requires valid user ID                                                                   | `{"name": ..., "description": ..., "creation_time": ...}`                 |
| `update_user`            | User   | **Name cannot be updated**; display name max 128 chars                                   | `None`                                                                    |
| `get_user_teams`         | User   | Lists teams where user is admin or member                                                | `[{"name": ..., "description": ..., "creation_time": ...}]`               |
| `create_team`            | Team   | Unique name, max 64 chars; description max 128 chars; valid admin ID                     | `{"id": "<team_id>"}`                                                     |
| `list_teams`             | Team   | Lists all teams with admin user ID                                                       | `[{"name": ..., "description": ..., "admin": ..., "creation_time": ...}]` |
| `describe_team`          | Team   | Requires valid team ID                                                                   | `{"name": ..., "description": ..., "admin": ..., "creation_time": ...}]`  |
| `update_team`            | Team   | Unique name, max 64 chars; description max 128 chars                                     | `None`                                                                    |
| `add_users_to_team`      | Team   | Max 50 users per request; team capacity capped at 50 members                             | `None`                                                                    |
| `remove_users_from_team` | Team   | Max 50 users per request; removes specified members                                      | `None`                                                                    |
| `list_team_users`        | Team   | Lists all members of the team                                                            | `[{"id": ..., "name": ..., "display_name": ...}]`                         |
| `create_board`           | Board  | Name unique per team, max 64 chars; description max 128 chars                            | `{"id": "<board_id>"}`                                                    |
| `close_board`            | Board  | **All tasks must be marked COMPLETE**; board must be OPEN; records `end_time`            | `None`                                                                    |
| `add_task`               | Board  | **Can only add to OPEN board**; title unique per board, max 64 chars; desc max 128 chars | `{"id": "<task_id>"}`                                                     |
| `update_task_status`     | Board  | Status must be `OPEN`, `IN_PROGRESS`, or `COMPLETE`                                      | `None`                                                                    |
| `list_boards`            | Board  | **Filters strictly for OPEN boards** of the specified team                               | `[{"id": ..., "name": ...}]`                                              |
| `export_board`           | Board  | Exports ASCII Kanban text report to `out/board_<id>.txt`                                 | `{"out_file": "<filename>"}`                                              |

---

## 5. Installation & Verification

### Prerequisites

- Python 3.10+
- Django (`Django>=5.0`)

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
# Run the complete Django test suite (27 test cases)
python manage.py test

# Run the standalone end-to-end verification script
python test_standalone.py
```

### Running the Django Server (Optional)

```bash
python manage.py runserver
```

All API endpoints are accessible under `/api/` (e.g. `POST /api/users/create/`, `GET /api/users/`, etc.).
