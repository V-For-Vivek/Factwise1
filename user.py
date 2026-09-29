import json
from django.db import models
from user_base import UserBase
from planner.models import UserModel, TeamModel


class User(UserBase):

    def create_user(self, request: str) -> str:
        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request : {e}")

        if not isinstance(data, dict):
            raise ValueError("Request body must be JSON object")

        name = data["name"]
        display_name = data["display_name"]

        if not isinstance(name, str) or not isinstance(display_name, str):
            raise ValueError("Field 'name' and 'display_name' must be string")

        name = name.strip()
        display_name = display_name.strip()

        if not name or not display_name:
            raise ValueError(
                "Field 'name' and 'display_name' is cannot be empty or whitespace"
            )

        if len(name) > 64 or len(display_name) > 64:
            raise ValueError("Field 'name' and 'display_name' can be max 64 characters")

        if UserModel.objects.filter(name=name).exists():
            raise ValueError(f"User with name '{name}' already exists")

        user = UserModel.objects.create(name=name, display_name=display_name)
        return json.dumps({"id": str(user.id)})  # type: ignore

    def list_users(self) -> str:

        users = UserModel.objects.all().order_by("id")
        result = [
            {
                "name": u.name,
                "display_name": u.display_name,
                "creation_time": u.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for u in users
        ]
        return json.dumps(result)

    def describe_user(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON request : {e}")

        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Request must be JSON object containing 'id'")

        user_id = data["id"]
        try:
            user = UserModel.objects.get(id=user_id)
        except (UserModel.DoesNotExist, ValueError, TypeError) as e:
            raise ValueError(f"User with id '{user_id}' does not exist")

        return json.dumps(
            {
                "name": user.name,
                "display_name": user.display_name,
                "creation_time": user.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def update_user(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request: {e}")

        if not isinstance(data, dict) or "id" not in data or "user" not in data:
            raise ValueError("Request must contain 'id' and 'user' fields")

        user_id = data["id"]
        user_data = data["user"]

        if not isinstance(user_data, dict):
            raise ValueError("Field 'user' must be an object")

        try:
            user = UserModel.objects.get(id=user_id)
        except (UserModel.DoesNotExist, ValueError, TypeError) as e:
            raise ValueError(f"User with id '{user_id}' does not exists")

        if "name" in user_data:
            requested_name = user_data["name"]
            if requested_name != user.name:
                raise ValueError("User name cannot be updated")
            if len(requested_name) > 64:
                raise ValueError("User name can be max 64 characters")

        if "display_name" in user_data:
            display_name = user_data["display_name"]
            if not isinstance(display_name, str):
                raise ValueError("Display name must be string")
            if len(display_name) > 128:
                raise ValueError("Display name can be max 128 characters")
            user.display_name = display_name

        user.save()
        return json.dumps({"status": "success"})

    def get_user_teams(self, request: str) -> str:

        try:
            data = json.loads(request)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Invalid JSON Request: {e}")

        if not isinstance(data, dict) or "id" not in data:
            raise ValueError("Request must be JSON object containing 'id'")

        user_id = data["id"]

        try:
            user = UserModel.objects.get(id=user_id)
        except (UserModel.DoesNotExist, ValueError, TypeError) as e:
            raise ValueError(f"User with id '{id}' does not exist")

        teams = (
            TeamModel.objects.filter(models.Q(admin=user) | models.Q(members=user))
            .distinct()
            .order_by("id")
        )
        result = [
            {
                "name": t.name,
                "description": t.description,
                "creation_time": t.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for t in teams
        ]
        return json.dumps(result)
