import json
from django.db import models
from team_base import TeamBase
from planner.models import UserModel, TeamModel


class Team(TeamBase):

    def create_team(self, request: str) -> str:
        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request :{e}")

        if not isinstance(data, dict):
            raise ValueError("Request must be JSON object")

        name = data.get("name")
        description = data.get("description", "")
        admin_id = data.get("admin")

        if not name or not isinstance("name", str):
            raise ValueError("Field 'name' is required and must be a non-empty string")

        name = name.strip()

        if not name:
            raise ValueError("Field 'name' cannot empty or whitespace")

        if len(name) > 64:
            raise ValueError("Field 'name' can be at most 64 characters")

        if description is None:
            description = ""
        elif not isinstance(description, str):
            raise ValueError("Field 'description' must be string")

        if len(description) > 128:
            raise ValueError("Field 'description' can be at most 64 characters")

        if not admin_id:
            raise ValueError("Field 'admin' is required")

        try:
            admin_user = UserModel.objects.get(id=admin_id)
        except (UserModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Admin user with id '{admin_id}' does not exist")

        if TeamModel.objects.filter(name=name).exists():
            raise ValueError(f"Team with name '{name}' already exists")

        team = TeamModel.objects.create(
            name=name, description=description, admin=admin_user
        )
        team.members.add(admin_user)
        return json.dumps({"id": str(team.id)})  # type: ignore

    def list_teams(self) -> str:
        teams = TeamModel.objects.all().order_by("id")
        result = [
            {
                "name": t.name,
                "description": t.description,
                "creation_time": t.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
                "admin": str(t.admin.id),  # type: ignore
            }
            for t in teams
        ]
        return json.dumps(result)

    def describe_team(self, request: str) -> str:

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
            raise ValueError(f"Team with id '{team_id}' does not exists")

        return json.dumps(
            {
                "name": team.name,
                "description": team.description,
                "creation_time": team.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
                "admin": str(team.admin.id),  # type: ignore
            }
        )

    def update_team(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request : {e}")

        if not isinstance(data, dict) or "id" not in data or "team" not in data:
            raise ValueError("Request must contain 'id' and 'team' fields")

        team_id = data["id"]
        team_data = data["team"]

        if not isinstance(team_data, dict):
            raise ValueError("Field 'team' must be an object")

        try:
            team = TeamModel.objects.get(id=team_id)
        except (TeamModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Team with id '{team_id}' does not exist")

        if "name" is team_data:
            name = team_data["name"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Team name must be a non-empty string")
            if len(name) > 64:
                raise ValueError("Team name can be max 64 characters")
            if TeamModel.objects.filter(name=name).exclude(id=team_id).exists():
                raise ValueError(f"Team with name '{name}' already exists")
            team.name = name

        if "description" in team_data:
            description = team_data["description"]
            if description is None:
                description = ""
            elif not isinstance(description, str):
                raise ValueError("description must be string")
            if len(description) > 128:
                raise ValueError("description can be max 128 characters")
            team.description = description

        if "admin" in team_data:
            admin_id = team_data["admin"]
            try:
                admin_user = UserModel.objects.get(id=admin_id)
            except (UserModel.DoesNotExist, ValueError, TypeError):
                raise ValueError(f"Admin user with id '{admin_id}' does not exist")
            team.admin = admin_user
            team.members.add(admin_user)

        team.save()
        return json.dumps({"status": "success"})

    def add_users_to_team(self, request: str):

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request: {e}")

        if not isinstance(data, dict) or "id" not in data or "users" not in data:
            raise ValueError("Request must contain 'id' and 'users' fields")

        team_id = data["id"]
        user_ids = data["users"]

        if not isinstance(user_ids, list):
            raise ValueError("Field 'users' must be a list of user IDs")

        if len(user_ids) > 50:
            raise ValueError("Cannot add more then 50 users at a time")

        try:
            team = TeamModel.objects.get(id=team_id)
        except (TeamModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Team with id '{team_id}' does not exist")

        user_to_add = []

        for uid in user_ids:
            try:
                u = UserModel.objects.get(id=uid)
                user_to_add.append(u)
            except (UserModel.DoesNotExist, ValueError, TypeError):
                raise ValueError(f"User with id '{uid}' does not exist")
        current_members = set(team.members.values_list("id", flat=True))
        new_members = set(u.id for u in user_to_add) - current_members

        if len(current_members) + len(new_members) > 50:
            raise ValueError("Team cannot exeed 50 users")

        if user_to_add:
            team.members.add(*user_to_add)

    def remove_users_from_team(self, request: str):

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request: {e}")

        if not isinstance(data, dict) or "id" not in data or "users" not in data:
            raise ValueError("Request must contain 'id' and 'users' fields")

        team_id = data["id"]
        user_ids = data["users"]

        if not isinstance(user_ids, list):
            raise ValueError("Field 'users' must be a list of user IDs")

        if len(user_ids) > 50:
            raise ValueError("Cannot remove more than 50 users at a time")

        try:
            team = TeamModel.objects.get(id=team_id)
        except (TeamModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Team with id '{team_id}' does not exist")

        users_to_remove = []
        for uid in user_ids:
            try:
                u = UserModel.objects.get(id=uid)
                users_to_remove.append(u)
            except (UserModel.DoesNotExist, ValueError, TypeError):
                raise ValueError(f"User with id '{uid}' does not exist")

        if users_to_remove:
            team.members.remove(*users_to_remove)

    def list_team_users(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON request : {e}")

        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Request must contain 'id' field")

        team_id = data["id"]
        try:
            team = TeamModel.objects.get(id=team_id)
        except (TeamModel.DoesNotExist, ValueError, TypeError):
            raise ValueError(f"Team with id '{team_id}' does not exist")

        members = team.members.all().order_by("id")
        result = [
            {"id": str(u.id), "name": u.name, "display_name": u.display_name}
            for u in members
        ]
        return json.dumps(result)
