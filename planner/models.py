from django.db import models
from django.utils import timezone


# Create your models here.
class UserModel(models.Model):
    name = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128)
    creation_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.display_name


class TeamModel(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=128, blank=True, default="")
    admin = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name="administered_teams"
    )
    members = models.ManyToManyField(UserModel, related_name="teams", blank=True)
    creation_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class BoardModel(models.Model):
    STATUS_CHOICES = [("OPEN", "open"), ("CLOSED", "closed")]

    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=128)
    team = models.ForeignKey(TeamModel, on_delete=models.CASCADE, related_name="board")
    creation_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("team", "name")
        ordering = ["id"]

    def __str__(self):
        return f"{self.team.name} - {self.name}"


class TaskModel(models.Model):

    STATUS_CHOICES = [
        ("OPEN", "OPEN"),
        ("IN_PROGRESS", "IN_PROGRESS"),
        ("COMPLETE", "COMPLETE"),
    ]

    title = models.CharField(max_length=64)
    description = models.CharField(max_length=128, blank=True, default="")
    board = models.ForeignKey(
        BoardModel, on_delete=models.CASCADE, related_name="tasks"
    )
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="tasks")
    creation_time = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    class Meta:
        unique_together = ("board", "title")
        ordering = ["id"]

    def __str__(self):
        return f"{self.board.name} - {self.title}"
