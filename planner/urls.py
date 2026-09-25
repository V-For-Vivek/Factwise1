from django.urls import path
from . import views

urlpatterns = [
    # User endpoints
    path("users/create/", views.user_create, name="user_create"),
    path("users/", views.user_list, name="user_list"),
    path("users/describe/", views.user_describe, name="user_describe"),
    path("users/update/", views.user_update, name="user_update"),
    path("users/teams/", views.user_teams, name="user_teams"),
    # Team endpoints
    path("teams/create/", views.team_create, name="team_create"),
    path("teams/", views.team_list, name="team_list"),
    path("teams/describe/", views.team_describe, name="team_describe"),
    path("teams/update/", views.team_update, name="team_update"),
    path("teams/add-users/", views.team_add_users, name="team_add_users"),
    path("teams/remove-users/", views.team_remove_users, name="team_remove_users"),
    path("teams/users/", views.team_users, name="team_users"),
    # Project Board endpoints
    path("boards/create/", views.board_create, name="board_create"),
    path("boards/close/", views.board_close, name="board_close"),
    path("boards/tasks/add/", views.task_add, name="task_add"),
    path(
        "boards/tasks/update-status/",
        views.task_update_status,
        name="task_update_status",
    ),
    path("boards/list/", views.board_list, name="board_list"),
    path("boards/export/", views.board_export, name="board_export"),
]
