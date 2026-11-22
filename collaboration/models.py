
#Part 1 — Gestion des groupes
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Group(models.Model):

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('full', 'Full'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups'
    )

    max_members = models.PositiveIntegerField(default=5)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='open'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_active_members_count(self):
        return self.members.filter(status='active').count()

    def is_full(self):
        return self.get_active_members_count() >= self.max_members
    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ['-created_at']

    

class GroupMember(models.Model):

    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('left', 'Left'),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='members'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')
        verbose_name = "Group Member"
        verbose_name_plural = "Group Members"

    def __str__(self):
        return f"{self.user} - {self.group}"

    
class GroupInvitation(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_group_invitations'
    )

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_group_invitations'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    responded_at = models.DateTimeField(
        null=True,
        blank=True
    )
    class Meta:
        verbose_name = "Group Invitation"
        verbose_name_plural = "Group Invitations"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.invited_user} - {self.group} ({self.status})"


class TeamContract(models.Model):

    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name='contract'
    )

    rules = models.TextField()
    objectives = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Team Contract"
        verbose_name_plural = "Team Contracts"
        ordering = ['-created_at']

    def __str__(self):
        return f"Contract - {self.group.name}"

class ContractAcceptance(models.Model):

    contract = models.ForeignKey(
        TeamContract,
        on_delete=models.CASCADE,
        related_name='acceptances'
    )

    member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name='contract_acceptances'
    )

    accepted = models.BooleanField(default=False)

    accepted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('contract', 'member')
        verbose_name = "Contract Acceptance"
        verbose_name_plural = "Contract Acceptances"

    def __str__(self):
        return f"{self.member.user} - {self.contract.group.name}"

#2. Gestion des projets et tâches
class Project(models.Model):

    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name='project'
    )

    start_date = models.DateField()

    deadline = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planning'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class ProjectRole(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='roles'
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'name'],
                name='unique_project_role'
            )
        ]
        verbose_name = "Project Role"
        verbose_name_plural = "Project Roles"
        ordering = ['project__title', 'name']

    def __str__(self):
        return f"{self.name} - {self.project.title}"

class ProjectMember(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members'
    )

    group_member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name='project_assignments'
    )

    role = models.ForeignKey(
        ProjectRole,
        on_delete=models.PROTECT,
        related_name='assigned_members'
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'group_member'],
                name='unique_project_member'
            )
        ]
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"
        ordering = ['project__title', 'role__name']

    def __str__(self):
        return f"{self.group_member.user} - {self.role.name}"
class Task(models.Model):

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('completed', 'Completed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='todo'
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    start_date = models.DateField()
    deadline = models.DateField()

    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Project Task"
        verbose_name_plural = "Project Tasks"
        ordering = ['deadline']
    def __str__(self):
        return self.title
    
class TaskAssignment(models.Model):

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    project_member = models.ForeignKey(
        ProjectMember,
        on_delete=models.CASCADE,
        related_name='task_assignments'
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['task', 'project_member'],
                name='unique_task_assignment'
            )
        ]
        verbose_name = "Task Assignment"
        verbose_name_plural = "Task Assignments"
        ordering = ['task__deadline']

    def __str__(self):
        return f"{self.project_member.group_member.user} - {self.task.title}"

class Meeting(models.Model):

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='meetings'
    )

    title = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    location = models.CharField(
        max_length=200,
        blank=True
    )

    meeting_link = models.URLField(
        blank=True
    )

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_meetings'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Project Meeting"
        verbose_name_plural = "Project Meetings"
        ordering = ['-date', '-start_time']
    def __str__(self):
        return self.title

class MeetingAttendance(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    group_member = models.ForeignKey(
        GroupMember,
        on_delete=models.CASCADE,
        related_name='meeting_attendances'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    responded_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['meeting', 'group_member'],
                name='unique_meeting_attendance'
            )
        ]
        verbose_name = "Meeting Attendance"
        verbose_name_plural = "Meeting Attendances"
        ordering = ['meeting__date', 'meeting__start_time']

    def __str__(self):
        return f"{self.group_member.user} - {self.meeting.title}"

class MeetingMinutes(models.Model):

    meeting = models.OneToOneField(
        Meeting,
        on_delete=models.CASCADE,
        related_name='minutes'
    )

    discussion_summary = models.TextField()

    decisions = models.TextField(blank=True)

    action_items = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_meeting_minutes'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Meeting Minutes"
        verbose_name_plural = "Meeting Minutes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Minutes - {self.meeting.title}"

class Decision(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='decisions_list'
    )

    title = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    responsible_member = models.ForeignKey(
        GroupMember,
        on_delete=models.SET_NULL,
        null=True,
        related_name='responsible_decisions'
    )

    deadline = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_decisions'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Meeting Decision"
        verbose_name_plural = "Meeting Decisions"
        ordering = ['deadline', '-created_at']

    def __str__(self):
        return self.title

class ContributionEvaluation(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )

    project_member = models.ForeignKey(
        ProjectMember,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )

    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='given_evaluations'
    )

    task_completion_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    work_quality_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    collaboration_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    deadline_respect_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])

    feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['project', 'project_member'],
                name='unique_member_evaluation_per_project'
            )
        ]
        verbose_name = "Contribution Evaluation"
        verbose_name_plural = "Contribution Evaluations"
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"Evaluation of {self.project_member.group_member.user} "
            f"- {self.project.title}"
        )

    @property
    def overall_score(self):
        return round(
            (
                self.task_completion_score
                + self.work_quality_score
                + self.collaboration_score
                + self.deadline_respect_score
            ) / 4,
            2
        )
