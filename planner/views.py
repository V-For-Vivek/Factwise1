import json
from django.http import (
    HttpResponseBadRequest,
    JsonResponse,
    HttpResponseNotFound,
    HttpResponse,
)
from django.views.decorators.csrf import csrf_exempt
from user import User
from team import Team
from project_board import ProjectBoard

user_service = User()
team_service = Team()
board_service = ProjectBoard()


def _get_request_body(request):
    if request.body:
        return request.body.decode("utf-8")
    if request.method == "GET":
        return json.dumps(dict(request.GET))
    return "{}"


@csrf_exempt
def user_create(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST")
    try:
        res = user_service.create_user(_get_request_body(request))
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def user_list(request):
    if request.method != "GET":
        return HttpResponseBadRequest("Method not allowed. Use GET.")
    res = user_service.list_users()
    return HttpResponse(res, content_type="application/json")


@csrf_exempt
def user_describe(request):
    try:
        body = _get_request_body(request)
        res = user_service.describe_user(body)
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def user_update(request):
    if request.method not in ["POST", "PUT"]:
        return HttpResponseBadRequest("Method not allowed. Use POST or PUT.")
    try:
        user_service.update_user(_get_request_body(request))
        return HttpResponse(
            json.dumps({"status": "success"}), content_type="application/json"
        )
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def user_teams(request):
    try:
        body = _get_request_body(request)
        res = user_service.get_user_teams(body)
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


# Teams
@csrf_exempt
def team_create(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. User POST.")
    try:
        res = team_service.create_team(_get_request_body(request))
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def team_list(request):
    if request.method != "GET":
        return HttpResponseBadRequest("Method not allowed. Use GET.")
    res = team_service.list_teams()
    return HttpResponseBadRequest(res, content_type="application/json")


@csrf_exempt
def team_describe(request):
    try:
        body = _get_request_body(request)
        res = team_service.describe_team(body)
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def team_update(request):
    if request.method not in ["POST", "PUT"]:
        return HttpResponseBadRequest("Method not allowed. Use POST or PUT")
    try:
        status = team_service.update_team(_get_request_body(request))
        return HttpResponse(status, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def team_add_users(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")
    try:
        team_service.add_users_to_team(_get_request_body(request))
        return HttpResponse(
            json.dumps({"status": "success"}), content_type="application/json"
        )
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def team_remove_users(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")
    try:
        team_service.remove_users_from_team(_get_request_body(request))
        return HttpResponse(
            json.dumps({"status": "success"}), content_type="application/json"
        )
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def team_users(request):
    try:
        body = _get_request_body(request)
        res = team_service.list_team_users(body)
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


# Project Boards


@csrf_exempt
def board_create(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")
    try:
        res = board_service.create_board(_get_request_body(request))
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def board_close(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")
    try:
        status = board_service.close_board(_get_request_body(request))
        return HttpResponse(status, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def task_add(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")
    try:
        res = board_service.add_task(_get_request_body(request))
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def task_update_status(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Method not allowed. Use POST.")
    try:
        board_service.update_task_status(_get_request_body(request))
        return HttpResponse(
            json.dumps({"status": "success"}), content_type="application/json"
        )
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def board_list(request):
    try:
        body = _get_request_body(request)
        res = board_service.list_boards(body)
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )


@csrf_exempt
def board_export(request):
    try:
        body = _get_request_body(request)
        res = board_service.export_board(body)
        return HttpResponse(res, content_type="application/json")
    except ValueError as e:
        return HttpResponseBadRequest(
            json.dumps({"error": str(e)}), content_type="application/json"
        )
