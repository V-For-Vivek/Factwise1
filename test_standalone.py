"""
Standalone test script validating all API operations and constraints
without relying on Django's test runner.
Can be executed repeatedly.
"""

import json
import os
import sys
import uuid

# Ensure root path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "factwise_project.settings")

import django

django.setup()

from user import User
from team import Team
from project_board import ProjectBoard


def run_all_tests():
    print("Starting Standalone API Tests...")
    user_api = User()
    team_api = Team()
    board_api = ProjectBoard()

    run_id = uuid.uuid4().hex[:6]
    alice_name = f"alice_{run_id}"
    bob_name = f"bob_{run_id}"
    team_name = f"Team_{run_id}"
    board_name = f"Board_{run_id}"

    # 1. User Tests
    print("\n--- Testing User API ---")
    u1_res = user_api.create_user(
        json.dumps({"name": alice_name, "display_name": "Alice S."})
    )
    u1_id = json.loads(u1_res)["id"]
    print(f"Created user 1 with ID: {u1_id} ({alice_name})")

    u2_res = user_api.create_user(
        json.dumps({"name": bob_name, "display_name": "Bob S."})
    )
    u2_id = json.loads(u2_res)["id"]
    print(f"Created user 2 with ID: {u2_id} ({bob_name})")

    # Duplicate check
    try:
        user_api.create_user(
            json.dumps({"name": alice_name, "display_name": "Alice Duplicate"})
        )
        assert False, "Should have failed on duplicate name"
    except ValueError as e:
        print(f"Verified duplicate user name rejection: {e}")

    # Describe user
    u1_desc = json.loads(user_api.describe_user(json.dumps({"id": u1_id})))
    assert u1_desc["name"] == alice_name
    assert u1_desc["display_name"] == "Alice S."
    print("Verified describe_user")

    # Update user display_name
    user_api.update_user(
        json.dumps(
            {"id": u1_id, "user": {"name": alice_name, "display_name": "Alice Senior"}}
        )
    )
    u1_desc_updated = json.loads(user_api.describe_user(json.dumps({"id": u1_id})))
    assert u1_desc_updated["display_name"] == "Alice Senior"
    print("Verified update_user display name")

    # Update user name immutability check
    try:
        user_api.update_user(
            json.dumps(
                {
                    "id": u1_id,
                    "user": {
                        "name": f"{alice_name}_mod",
                        "display_name": "Alice Senior",
                    },
                }
            )
        )
        assert False, "Should have failed when attempting to update user name"
    except ValueError as e:
        print(f"Verified user name immutability: {e}")

    # List users
    users_list = json.loads(user_api.list_users())
    assert len(users_list) >= 2
    print("Verified list_users")

    # 2. Team Tests
    print("\n--- Testing Team API ---")
    t1_res = team_api.create_team(
        json.dumps(
            {
                "name": team_name,
                "description": "Dev team for standalone tests",
                "admin": u1_id,
            }
        )
    )
    t1_id = json.loads(t1_res)["id"]
    print(f"Created team with ID: {t1_id} ({team_name})")

    # Duplicate team name
    try:
        team_api.create_team(
            json.dumps({"name": team_name, "description": "Duplicate", "admin": u2_id})
        )
        assert False, "Should have failed on duplicate team name"
    except ValueError as e:
        print(f"Verified duplicate team name rejection: {e}")

    # Add user to team
    team_api.add_users_to_team(json.dumps({"id": t1_id, "users": [u2_id]}))
    team_users = json.loads(team_api.list_team_users(json.dumps({"id": t1_id})))
    member_ids = [m["id"] for m in team_users]
    assert u1_id in member_ids and u2_id in member_ids
    print("Verified add_users_to_team and list_team_users")

    # Check user teams
    u2_teams = json.loads(user_api.get_user_teams(json.dumps({"id": u2_id})))
    assert any(t["name"] == team_name for t in u2_teams)
    print("Verified get_user_teams")

    # 3. Project Board Tests
    print("\n--- Testing Project Board API ---")
    b1_res = board_api.create_board(
        json.dumps(
            {"name": board_name, "description": "Q4 deliverables", "team_id": t1_id}
        )
    )
    b1_id = json.loads(b1_res)["id"]
    print(f"Created board with ID: {b1_id} ({board_name})")

    # Duplicate board name for same team
    try:
        board_api.create_board(
            json.dumps(
                {"name": board_name, "description": "Duplicate", "team_id": t1_id}
            )
        )
        assert False, "Should have failed on duplicate board name for team"
    except ValueError as e:
        print(f"Verified duplicate board name per team rejection: {e}")

    # Add tasks
    task1_res = board_api.add_task(
        json.dumps(
            {
                "title": "Backend Schema",
                "description": "Design database models",
                "user_id": u1_id,
                "board_id": b1_id,
            }
        )
    )
    task1_id = json.loads(task1_res)["id"]

    task2_res = board_api.add_task(
        json.dumps(
            {
                "title": "Frontend UI",
                "description": "Design dashboard UI",
                "user_id": u2_id,
                "board_id": b1_id,
            }
        )
    )
    task2_id = json.loads(task2_res)["id"]
    print(f"Created tasks: {task1_id}, {task2_id}")

    # Duplicate task title on same board
    try:
        board_api.add_task(
            json.dumps(
                {
                    "title": "Backend Schema",
                    "description": "Duplicate task",
                    "user_id": u2_id,
                    "board_id": b1_id,
                }
            )
        )
        assert False, "Should have failed on duplicate task title"
    except ValueError as e:
        print(f"Verified duplicate task title rejection: {e}")

    # Attempt to close board with OPEN tasks
    try:
        board_api.close_board(json.dumps({"id": b1_id}))
        assert False, "Should have failed closing board with OPEN tasks"
    except ValueError as e:
        print(f"Verified closing board with incomplete tasks rejection: {e}")

    # Update task statuses
    board_api.update_task_status(json.dumps({"id": task1_id, "status": "COMPLETE"}))
    board_api.update_task_status(json.dumps({"id": task2_id, "status": "IN_PROGRESS"}))

    # Still incomplete
    try:
        board_api.close_board(json.dumps({"id": b1_id}))
        assert False, "Should have failed closing board with IN_PROGRESS tasks"
    except ValueError as e:
        print(f"Verified closing board with IN_PROGRESS tasks rejection: {e}")

    # Complete task 2
    board_api.update_task_status(json.dumps({"id": task2_id, "status": "COMPLETE"}))

    # Export board before closing (both tasks COMPLETE → 100%)
    export_res = board_api.export_board(json.dumps({"id": b1_id}))
    out_file = json.loads(export_res)["out_file"]
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", out_file)
    print(f"Exported board to: out/{out_file}")

    # --- Validate progress bar in the exported file ---
    with open(out_path, encoding="utf-8") as f:
        report_text = f.read()

    # Expect 100% → all 25 filled blocks, zero empty blocks
    assert "█" * 25 in report_text, (
        "Progress bar should be fully filled (25 █) when all tasks are COMPLETE, "
        f"but report contains:\n{report_text}"
    )
    assert "░" not in report_text.split("Progress:")[1].split("\n")[0], (
        "Progress bar should have no empty (░) blocks at 100% completion"
    )
    assert "100.0%" in report_text, "Percentage label should show 100.0%"
    print("Verified export_board progress bar at 100% completion")

    # Now close board
    board_api.close_board(json.dumps({"id": b1_id}))
    print("Successfully closed board!")

    # Verify board is not in list_boards (only OPEN boards listed)
    open_boards = json.loads(board_api.list_boards(json.dumps({"id": t1_id})))
    assert not any(b["id"] == b1_id for b in open_boards)
    print("Verified closed board is excluded from list_boards")

    # Cannot add task to CLOSED board
    try:
        board_api.add_task(
            json.dumps(
                {
                    "title": "Late Task",
                    "description": "Late addition",
                    "user_id": u1_id,
                    "board_id": b1_id,
                }
            )
        )
        assert False, "Should have failed adding task to CLOSED board"
    except ValueError as e:
        print(f"Verified rejection of adding task to CLOSED board: {e}")

    print("\nALL STANDALONE API TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_tests()
