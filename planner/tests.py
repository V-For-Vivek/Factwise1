import json
import os
from django.test import TestCase, Client
from django.conf import settings
from user import User
from team import Team
from project_board import ProjectBoard
from planner.models import UserModel, TeamModel, BoardModel, TaskModel


class UserApiTests(TestCase):
    def setUp(self):
        self.user_api = User()

    def test_create_user_success(self):
        payload = json.dumps({"name": "john_doe", "display_name": "John Doe"})
        res = self.user_api.create_user(payload)
        data = json.loads(res)
        self.assertIn("id", data)
        self.assertTrue(UserModel.objects.filter(name="john_doe").exists())

    def test_create_user_duplicate_name(self):
        payload = json.dumps({"name": "john_doe", "display_name": "John Doe"})
        self.user_api.create_user(payload)
        with self.assertRaises(ValueError):
            self.user_api.create_user(payload)

    def test_create_user_name_length_constraint(self):
        payload = json.dumps({"name": "a" * 65, "display_name": "Too Long"})
        with self.assertRaises(ValueError):
            self.user_api.create_user(payload)

    def test_create_user_display_name_length_constraint(self):
        payload = json.dumps({"name": "valid_name", "display_name": "b" * 65})
        with self.assertRaises(ValueError):
            self.user_api.create_user(payload)

    def test_list_users(self):
        self.user_api.create_user(
            json.dumps({"name": "user1", "display_name": "User One"})
        )
        self.user_api.create_user(
            json.dumps({"name": "user2", "display_name": "User Two"})
        )
        res = self.user_api.list_users()
        users = json.loads(res)
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0]["name"], "user1")
        self.assertEqual(users[1]["name"], "user2")
        self.assertIn("creation_time", users[0])

    def test_describe_user(self):
        res = self.user_api.create_user(
            json.dumps({"name": "alice", "display_name": "Alice Wonderland"})
        )
        uid = json.loads(res)["id"]
        desc_res = self.user_api.describe_user(json.dumps({"id": uid}))
        desc = json.loads(desc_res)
        self.assertEqual(desc["name"], "alice")
        self.assertEqual(desc["display_name"], "Alice Wonderland")
        self.assertIn("creation_time", desc)

    def test_describe_user_not_found(self):
        with self.assertRaises(ValueError):
            self.user_api.describe_user(json.dumps({"id": "99999"}))

    def test_update_user_display_name(self):
        res = self.user_api.create_user(
            json.dumps({"name": "bob", "display_name": "Bob Old"})
        )
        uid = json.loads(res)["id"]
        update_req = json.dumps(
            {
                "id": uid,
                "user": {
                    "name": "bob",
                    "display_name": "Bob New " + "x" * 100,  # Up to 128 chars allowed
                },
            }
        )
        self.user_api.update_user(update_req)
        desc = json.loads(self.user_api.describe_user(json.dumps({"id": uid})))
        self.assertTrue(desc["display_name"].startswith("Bob New"))

    def test_update_user_name_immutable(self):
        res = self.user_api.create_user(
            json.dumps({"name": "charlie", "display_name": "Charlie"})
        )
        uid = json.loads(res)["id"]
        update_req = json.dumps(
            {"id": uid, "user": {"name": "charlie_renamed", "display_name": "Charlie"}}
        )
        with self.assertRaises(ValueError):
            self.user_api.update_user(update_req)

    def test_update_user_display_name_exceeds_128(self):
        res = self.user_api.create_user(
            json.dumps({"name": "david", "display_name": "David"})
        )
        uid = json.loads(res)["id"]
        update_req = json.dumps(
            {"id": uid, "user": {"name": "david", "display_name": "d" * 129}}
        )
        with self.assertRaises(ValueError):
            self.user_api.update_user(update_req)


class TeamApiTests(TestCase):
    def setUp(self):
        self.user_api = User()
        self.team_api = Team()
        user_res = self.user_api.create_user(
            json.dumps({"name": "admin_user", "display_name": "Admin User"})
        )
        self.admin_id = json.loads(user_res)["id"]

    def test_create_team_success(self):
        req = json.dumps(
            {
                "name": "Engineering",
                "description": "Core dev team",
                "admin": self.admin_id,
            }
        )
        res = self.team_api.create_team(req)
        team_id = json.loads(res)["id"]
        self.assertTrue(TeamModel.objects.filter(id=team_id).exists())

    def test_create_team_duplicate_name(self):
        req = json.dumps(
            {
                "name": "Engineering",
                "description": "Core dev team",
                "admin": self.admin_id,
            }
        )
        self.team_api.create_team(req)
        with self.assertRaises(ValueError):
            self.team_api.create_team(req)

    def test_create_team_invalid_admin(self):
        req = json.dumps(
            {"name": "Marketing", "description": "Marketing team", "admin": "99999"}
        )
        with self.assertRaises(ValueError):
            self.team_api.create_team(req)

    def test_list_and_describe_teams(self):
        req = json.dumps(
            {"name": "Design", "description": "UI/UX", "admin": self.admin_id}
        )
        team_id = json.loads(self.team_api.create_team(req))["id"]

        teams = json.loads(self.team_api.list_teams())
        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0]["name"], "Design")
        self.assertEqual(teams[0]["admin"], self.admin_id)

        desc = json.loads(self.team_api.describe_team(json.dumps({"id": team_id})))
        self.assertEqual(desc["name"], "Design")
        self.assertEqual(desc["description"], "UI/UX")
        self.assertEqual(desc["admin"], self.admin_id)

    def test_add_and_remove_users_from_team(self):
        team_id = json.loads(
            self.team_api.create_team(
                json.dumps(
                    {
                        "name": "DevOps",
                        "description": "Infra team",
                        "admin": self.admin_id,
                    }
                )
            )
        )["id"]

        u1 = json.loads(
            self.user_api.create_user(
                json.dumps({"name": "dev1", "display_name": "Dev 1"})
            )
        )["id"]
        u2 = json.loads(
            self.user_api.create_user(
                json.dumps({"name": "dev2", "display_name": "Dev 2"})
            )
        )["id"]

        # Add users
        self.team_api.add_users_to_team(json.dumps({"id": team_id, "users": [u1, u2]}))

        members = json.loads(self.team_api.list_team_users(json.dumps({"id": team_id})))
        member_ids = [m["id"] for m in members]
        self.assertIn(u1, member_ids)
        self.assertIn(u2, member_ids)
        self.assertIn(self.admin_id, member_ids)

        # Remove user
        self.team_api.remove_users_from_team(json.dumps({"id": team_id, "users": [u1]}))

        members_after = json.loads(
            self.team_api.list_team_users(json.dumps({"id": team_id}))
        )
        member_ids_after = [m["id"] for m in members_after]
        self.assertNotIn(u1, member_ids_after)
        self.assertIn(u2, member_ids_after)

    def test_add_users_cap_50(self):
        team_id = json.loads(
            self.team_api.create_team(
                json.dumps(
                    {
                        "name": "LargeTeam",
                        "description": "Big team",
                        "admin": self.admin_id,
                    }
                )
            )
        )["id"]

        # Attempt to add 51 users in one request
        user_ids = []
        for i in range(51):
            uid = json.loads(
                self.user_api.create_user(
                    json.dumps({"name": f"u_{i}", "display_name": f"User {i}"})
                )
            )["id"]
            user_ids.append(uid)

        with self.assertRaises(ValueError):
            self.team_api.add_users_to_team(
                json.dumps({"id": team_id, "users": user_ids})
            )

    def test_team_total_members_cap_50(self):
        team_id = json.loads(
            self.team_api.create_team(
                json.dumps(
                    {
                        "name": "CapTeam",
                        "description": "Cap team",
                        "admin": self.admin_id,
                    }
                )
            )
        )["id"]

        # Admin is already 1 member. Add 49 members -> 50 total
        batch_1 = []
        for i in range(49):
            uid = json.loads(
                self.user_api.create_user(
                    json.dumps({"name": f"cap_u_{i}", "display_name": f"U {i}"})
                )
            )["id"]
            batch_1.append(uid)

        self.team_api.add_users_to_team(json.dumps({"id": team_id, "users": batch_1}))

        # Try to add 1 more member -> exceeds 50
        extra_uid = json.loads(
            self.user_api.create_user(
                json.dumps({"name": "extra_u", "display_name": "Extra"})
            )
        )["id"]
        with self.assertRaises(ValueError):
            self.team_api.add_users_to_team(
                json.dumps({"id": team_id, "users": [extra_uid]})
            )

    def test_get_user_teams(self):
        team_id = json.loads(
            self.team_api.create_team(
                json.dumps(
                    {
                        "name": "Alpha",
                        "description": "Alpha project",
                        "admin": self.admin_id,
                    }
                )
            )
        )["id"]

        teams = json.loads(
            self.user_api.get_user_teams(json.dumps({"id": self.admin_id}))
        )
        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0]["name"], "Alpha")


class ProjectBoardApiTests(TestCase):
    def setUp(self):
        self.user_api = User()
        self.team_api = Team()
        self.board_api = ProjectBoard()

        self.admin_id = json.loads(
            self.user_api.create_user(
                json.dumps({"name": "lead_user", "display_name": "Lead User"})
            )
        )["id"]
        self.dev_id = json.loads(
            self.user_api.create_user(
                json.dumps({"name": "dev_user", "display_name": "Dev User"})
            )
        )["id"]

        self.team_id = json.loads(
            self.team_api.create_team(
                json.dumps(
                    {
                        "name": "FrontendTeam",
                        "description": "UI Team",
                        "admin": self.admin_id,
                    }
                )
            )
        )["id"]
        self.team_api.add_users_to_team(
            json.dumps({"id": self.team_id, "users": [self.dev_id]})
        )

    def test_create_board_success(self):
        req = json.dumps(
            {
                "name": "Sprint 1",
                "description": "First sprint board",
                "team_id": self.team_id,
                "creation_time": "2026-09-01 10:00:00",
            }
        )
        res = self.board_api.create_board(req)
        board_id = json.loads(res)["id"]
        self.assertTrue(BoardModel.objects.filter(id=board_id, status="OPEN").exists())

    def test_create_board_duplicate_for_team(self):
        req = json.dumps(
            {
                "name": "Sprint 1",
                "description": "First sprint board",
                "team_id": self.team_id,
            }
        )
        self.board_api.create_board(req)
        with self.assertRaises(ValueError):
            self.board_api.create_board(req)

    def test_add_task_to_board(self):
        b_res = self.board_api.create_board(
            json.dumps(
                {"name": "Sprint 2", "description": "Board", "team_id": self.team_id}
            )
        )
        board_id = json.loads(b_res)["id"]

        task_res = self.board_api.add_task(
            json.dumps(
                {
                    "title": "Setup Navbar",
                    "description": "Build responsive navigation",
                    "user_id": self.dev_id,
                    "board_id": board_id,
                }
            )
        )
        task_id = json.loads(task_res)["id"]
        self.assertTrue(TaskModel.objects.filter(id=task_id, status="OPEN").exists())

    def test_add_task_title_unique_per_board(self):
        b_res = self.board_api.create_board(
            json.dumps(
                {"name": "Sprint 3", "description": "Board", "team_id": self.team_id}
            )
        )
        board_id = json.loads(b_res)["id"]

        self.board_api.add_task(
            json.dumps(
                {
                    "title": "Setup Auth",
                    "description": "Auth login",
                    "user_id": self.dev_id,
                    "board_id": board_id,
                }
            )
        )

        with self.assertRaises(ValueError):
            self.board_api.add_task(
                json.dumps(
                    {
                        "title": "Setup Auth",
                        "description": "Duplicate title",
                        "user_id": self.dev_id,
                        "board_id": board_id,
                    }
                )
            )

    def test_update_task_status(self):
        b_res = self.board_api.create_board(
            json.dumps(
                {"name": "Sprint 4", "description": "Board", "team_id": self.team_id}
            )
        )
        board_id = json.loads(b_res)["id"]
        t_res = self.board_api.add_task(
            json.dumps(
                {
                    "title": "Feature A",
                    "description": "Desc",
                    "user_id": self.dev_id,
                    "board_id": board_id,
                }
            )
        )
        task_id = json.loads(t_res)["id"]

        self.board_api.update_task_status(
            json.dumps({"id": task_id, "status": "IN_PROGRESS"})
        )
        task = TaskModel.objects.get(id=task_id)
        self.assertEqual(task.status, "IN_PROGRESS")

        self.board_api.update_task_status(
            json.dumps({"id": task_id, "status": "COMPLETE"})
        )
        task.refresh_from_db()
        self.assertEqual(task.status, "COMPLETE")

        with self.assertRaises(ValueError):
            self.board_api.update_task_status(
                json.dumps({"id": task_id, "status": "INVALID_STATUS"})
            )

    def test_close_board_constraints(self):
        b_res = self.board_api.create_board(
            json.dumps(
                {"name": "Sprint 5", "description": "Board", "team_id": self.team_id}
            )
        )
        board_id = json.loads(b_res)["id"]
        t_res = self.board_api.add_task(
            json.dumps(
                {
                    "title": "Task 1",
                    "description": "Desc",
                    "user_id": self.dev_id,
                    "board_id": board_id,
                }
            )
        )
        task_id = json.loads(t_res)["id"]

        # Board cannot be closed because Task 1 is OPEN
        with self.assertRaises(ValueError):
            self.board_api.close_board(json.dumps({"id": board_id}))

        # Mark task as COMPLETE
        self.board_api.update_task_status(
            json.dumps({"id": task_id, "status": "COMPLETE"})
        )

        # Now closing board succeeds
        self.board_api.close_board(json.dumps({"id": board_id}))
        board = BoardModel.objects.get(id=board_id)
        self.assertEqual(board.status, "CLOSED")
        self.assertIsNotNone(board.end_time)

        # Cannot close already closed board
        with self.assertRaises(ValueError):
            self.board_api.close_board(json.dumps({"id": board_id}))

        # Cannot add task to CLOSED board
        with self.assertRaises(ValueError):
            self.board_api.add_task(
                json.dumps(
                    {
                        "title": "New Task",
                        "description": "Desc",
                        "user_id": self.dev_id,
                        "board_id": board_id,
                    }
                )
            )

    def test_list_open_boards_only(self):
        b1_res = self.board_api.create_board(
            json.dumps(
                {"name": "Open Board", "description": "Board", "team_id": self.team_id}
            )
        )
        b2_res = self.board_api.create_board(
            json.dumps(
                {
                    "name": "Closed Board",
                    "description": "Board",
                    "team_id": self.team_id,
                }
            )
        )
        b2_id = json.loads(b2_res)["id"]
        self.board_api.close_board(json.dumps({"id": b2_id}))

        boards = json.loads(
            self.board_api.list_boards(json.dumps({"id": self.team_id}))
        )
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0]["name"], "Open Board")

    def test_export_board(self):
        b_res = self.board_api.create_board(
            json.dumps(
                {
                    "name": "Release Board",
                    "description": "Major release tasks",
                    "team_id": self.team_id,
                }
            )
        )
        board_id = json.loads(b_res)["id"]

        t1_id = json.loads(
            self.board_api.add_task(
                json.dumps(
                    {
                        "title": "Task Open",
                        "description": "Pending work",
                        "user_id": self.dev_id,
                        "board_id": board_id,
                    }
                )
            )
        )["id"]
        t2_id = json.loads(
            self.board_api.add_task(
                json.dumps(
                    {
                        "title": "Task InProg",
                        "description": "Active work",
                        "user_id": self.dev_id,
                        "board_id": board_id,
                    }
                )
            )
        )["id"]
        t3_id = json.loads(
            self.board_api.add_task(
                json.dumps(
                    {
                        "title": "Task Done",
                        "description": "Finished work",
                        "user_id": self.dev_id,
                        "board_id": board_id,
                    }
                )
            )
        )["id"]

        self.board_api.update_task_status(
            json.dumps({"id": t2_id, "status": "IN_PROGRESS"})
        )
        self.board_api.update_task_status(
            json.dumps({"id": t3_id, "status": "COMPLETE"})
        )

        export_res = self.board_api.export_board(json.dumps({"id": board_id}))
        export_data = json.loads(export_res)
        self.assertIn("out_file", export_data)
        out_file = export_data["out_file"]

        out_path = os.path.join(settings.BASE_DIR, "out", out_file)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("RELEASE BOARD", content)
        self.assertIn("FrontendTeam", content)
        self.assertIn("Task Open", content)
        self.assertIn("Task InProg", content)
        self.assertIn("Task Done", content)
        self.assertIn("Progress:", content)


class RestApiEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_and_team_rest_endpoints(self):
        # Create user via HTTP POST
        res = self.client.post(
            "/api/users/create/",
            data=json.dumps({"name": "rest_user", "display_name": "REST User"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        user_id = res.json()["id"]

        # List users via HTTP GET
        res = self.client.get("/api/users/")
        self.assertEqual(res.status_code, 200)
        users = res.json()
        self.assertTrue(any(u["name"] == "rest_user" for u in users))

        # Create team via HTTP POST
        res = self.client.post(
            "/api/teams/create/",
            data=json.dumps(
                {"name": "REST Team", "description": "Team via API", "admin": user_id}
            ),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        team_id = res.json()["id"]

        # Describe team
        res = self.client.post(
            "/api/teams/describe/",
            data=json.dumps({"id": team_id}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "REST Team")
