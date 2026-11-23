from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminDashboardGroupingTests(TestCase):
    def test_collaboration_models_are_grouped_by_workflow(self):
        user_model = get_user_model()
        user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.login(username="admin", password="test-password")

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        app_list = response.context["app_list"]
        groups = app_list[:3]
        self.assertEqual(
            [group["name"] for group in groups],
            [
                "Gestion des groupes",
                "Gestion des projets et tâches",
                "Organisation et suivi",
            ],
        )
        self.assertEqual(
            {
                group["name"]: {model["object_name"] for model in group["models"]}
                for group in groups
            },
            {
                "Gestion des groupes": {
                    "Group",
                    "GroupMember",
                    "GroupInvitation",
                    "TeamContract",
                    "ContractAcceptance",
                },
                "Gestion des projets et tâches": {
                    "Project",
                    "ProjectRole",
                    "ProjectMember",
                    "Task",
                    "TaskAssignment",
                },
                "Organisation et suivi": {
                    "Meeting",
                    "MeetingAttendance",
                    "MeetingMinutes",
                    "Decision",
                    "ContributionEvaluation",
                },
            },
        )
