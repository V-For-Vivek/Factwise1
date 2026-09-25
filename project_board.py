import os
import json
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.db import models
from project_board_base import ProjectBoardBase
from planner.models import UserModel, TeamModel, BoardModel, TaskModel


def parse_datetime(dt_str):
    """Helper to parse datetime strings or return current timezone-aware datetime."""
    if not dt_str or not isinstance(dt_str, str):
        return timezone.now()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
        except ValueError:
            pass

    try:
        dt = datetime.fromisoformat(dt_str)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
            return dt
    except Exception:
        return timezone.now()


class ProjectBoard(ProjectBoardBase):

    def create_board(self, request: str) -> str:
        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request : {e}")

        if not isinstance(data, dict):
            raise ValueError("Request must be JSON object")

        name = data.get("name")
        description = data.get("description")
        team_id = data.get("team_id")
        creation_time_str = data.get("creation_time")

        if not name or not isinstance(name, str):
            raise ValueError("Field 'name' is required and must be a non-empty string")
        name = name.strip()
        if not name:
            raise ValueError("Field 'name' cannot be empty or whitespaces")
        if len(name) > 64:
            raise ValueError("Field 'name' can be max 64 characters")

        if description is None:
            description = ""
        elif not isinstance(description, str):
            raise ValueError("Field 'description' must be string")
        if len(description) > 128:
            raise ValueError("Field 'description' can be max 128 characters")

        if not team_id:
            raise ValueError("Field 'team_id' is required")

        try:
            team = TeamModel.objects.get(id=team_id)
        except (TeamModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Team with id '{team_id}' does not exist")

        if BoardModel.objects.filter(team=team, name=name).exists():
            raise ValueError(
                f"Board with name '{name}' already exists for team '{team.name}'"
            )

        creation_time = parse_datetime(creation_time_str)

        board = BoardModel.objects.create(
            name=name,
            description=description,
            team=team,
            status="OPEN",
            creation_time=creation_time,
        )

        return json.dumps({"id": str(board.id)})  # type: ignore

    def close_board(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON request : {e}")

        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Request must JSON object containing 'id'")

        board_id = data["id"]

        try:
            board = BoardModel.objects.get(id=board_id)
        except (BoardModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Board with id '{board_id}' does not exist")

        if board.status == "CLOSED":
            raise ValueError("Board is already closed")

        incomplete_tasks = board.tasks.exclude(status="COMPLETE")  # type: ignore
        if incomplete_tasks.exists():
            count = incomplete_tasks.count()
            raise ValueError(
                f"Cannot close board: '{count}' task(s) are not marked as COMPLETE"
            )

        board.status = "CLOSED"
        board.end_time = timezone.now()
        board.save()

        return json.dumps({"status": "success"})

    def add_task(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON request : {e}")

        if not isinstance(data, dict):
            raise ValueError("Request must be JSON object")

        title = data.get("title")
        description = data.get("description")
        user_id = data.get("user_id")
        creation_time_str = data.get("creation_time")

        if not title or not isinstance(title, str):
            raise ValueError("Field 'title' is required and must be non-empty string")
        title = title.strip()
        if not title:
            raise ValueError("Field 'title' cannot be empty or whitespaces")
        if len(title) > 64:
            raise ValueError("Field 'title' can be max 64 characters")

        if description is None:
            description = ""
        elif not isinstance(description, str):
            raise ValueError("Field 'description' must be string")
        if len(description) > 128:
            raise ValueError("Field 'description' can be at most 128 characters")

        if not user_id:
            raise ValueError("Field 'user_id' is required")

        try:
            assigned_user = UserModel.objects.get(id=user_id)
        except (UserModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"User with id : '{user_id}' does not exist")

        board_id = data.get("board_id") or data.get("id") or data.get("board")
        board = None
        if board_id:
            try:
                board = BoardModel.objects.get(id=board_id)
            except (BoardModel.DoesNotExist, ValueError, TypeError):
                raise ValueError(f"Board with id '{board_id}' does not exist")
        else:
            user_teams = TeamModel.objects.filter(
                models.Q(admin=assigned_user) | models.Q(members=assigned_user)
            ).distinct()
            open_boards = BoardModel.objects.filter(team__in=user_teams, status="OPEN")
            if open_boards.count() == 1:
                board = open_boards.first()
            elif open_boards.count() > 1:
                raise ValueError(
                    "Multiple open boards found for user's teams. Please specify 'board_id'"
                )
            else:
                raise ValueError("Board identifier (board_id) is required to add task")

        if board.status != "OPEN":  # type: ignore
            raise ValueError("can only add task to OPEN board")

        if TaskModel.objects.filter(board=board, title=title).exists():
            raise ValueError(f"Task with title '{title}' already exists on board '{board.name}'")  # type: ignore

        creation_time = parse_datetime(creation_time_str)

        task = TaskModel.objects.create(
            title=title,
            description=description,
            board=board,
            user=assigned_user,
            status="OPEN",
            creation_time=creation_time,
        )

        return json.dumps({"id": str(task.id)})  # type: ignore

    def update_task_status(self, request: str):

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request : {e}")

        if not isinstance(data, dict) or "id" not in data and "status" not in data:
            raise ValueError("Request must contain 'id' and status fields")

        task_id = data["id"]
        status = data["status"]

        allowed_statuses = ["OPEN", "IN_PROGRESS", "COMPLETE"]
        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {', '.join(allowed_statuses)}"
            )

        try:
            task = TaskModel.objects.get(id=task_id)
        except (TaskModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Task with id '{task_id}' does not exist")

        task.status = status
        task.save()

    def list_boards(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request : {e}")

        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Request must contain 'id' field")

        team_id = data["id"]

        try:
            team = TeamModel.objects.get(id=team_id)
        except (TeamModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Team with id '{team_id}' does not exist")

        boards = BoardModel.objects.filter(team=team, status="OPEN").order_by("id")
        result = [{"id": str(b.id), "name": b.name} for b in boards]  # type: ignore
        return json.dumps(result)

    def export_board(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON request : {e}")

        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Request must contain 'id' for field")

        board_id = data["id"]
        try:
            board = BoardModel.objects.select_related("team", "team__admin").get(
                id=board_id
            )
        except (BoardModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Board with id '{board_id}' does not exist")

        tasks = list(board.tasks.select_related("user").order_by("id"))  # type: ignore
        total_tasks = len(tasks)
        open_tasks = [t for t in tasks if t.status == "OPEN"]
        in_progress_tasks = [t for t in tasks if t.status == "IN_PROGRESS"]
        completed_tasks = [t for t in tasks if t.status == "COMPLETE"]

        pct = 0.0
        if total_tasks > 0:
            pct = (len(completed_tasks) / total_tasks) * 100.0

        bar_len = 25
        filled_len = int(round(bar_len * pct / 100))
        progress_bar = "█" * filled_len + "░" * (bar_len - filled_len)

        out_dir = getattr(settings, "OUT_DIR", os.path.join(settings.BASE_DIR, "out"))
        os.makedirs(out_dir, exist_ok=True)
        file_name = f"board_{board_id}.txt"
        file_path = os.path.join(out_dir, file_name)

        created_str = board.creation_time.strftime("%Y-%m-%d %H:%M:%S")
        closed_str = (
            board.end_time.strftime("%Y-%m-%d %H:%M:%S") if board.end_time else "N/A"
        )

        sep = "=" * 80
        sub_sep = "-" * 80

        lines = [
            sep,
            f"  PROJECT BOARD REPORT: {board.name.upper()} (ID: {board.id})",  # type: ignore
            sep,
            f"  Team:        {board.team.name} (ID: {board.team.id})",  # type: ignore
            f"  Team Admin:  {board.team.admin.display_name} (@{board.team.admin.name})",
            f"  description: {board.description or '(None)'}",
            f"  Status:      [{board.status}]",
            f"  Created At:  {created_str}",
            f"  Closed At:   {closed_str}",
            sub_sep,
            f"  Progress:    [{progress_bar}] {pct:.1f}% ({len(completed_tasks)}/{total_tasks} Completed)",
            f"  Task Counts: Total: {total_tasks} | Open: {len(open_tasks)} | In Progress: {len(in_progress_tasks)} | Completed: {len(completed_tasks)}",
            sep,
            "",
        ]

        def format_task_section(section_title, task_list, icon):
            sec_lines = [
                f"{icon} {section_title} ({len(task_list)})",
                sub_sep,
            ]
            if not task_list:
                sec_lines.append("   (No Tasks in this column)")
            else:
                for idx, t in enumerate(task_list, 1):
                    created = t.creation_time.strftime("%Y-%m-%d %H:%M:%S")
                    sec_lines.append(f"  {idx}. [#{t.id}] {t.title}")
                    sec_lines.append(f"     description: {t.description or '(None)'}")
                    sec_lines.append(
                        f"     Assignee:    {t.user.display_name} (@{t.user.name})"
                    )
                    sec_lines.append(f"     Created:     {created}")
                    sec_lines.append(f"     Status:      {t.status}")
                    sec_lines.append("")
                sec_lines.append("")
            return sec_lines

        lines.extend(format_task_section("OPEN TASKS", open_tasks, "[OPEN]"))  # type: ignore
        lines.extend(format_task_section("IN PROGRESS TASKS", in_progress_tasks, "[IN PROGRESS]"))  # type: ignore
        lines.extend(format_task_section("COMPLETED TASKS", completed_tasks, "[COMPLETE]"))  # type: ignore
        lines.append(sep)
        lines.append(
            f" Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        lines.append(sep)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return json.dumps({"out_file": file_name})
