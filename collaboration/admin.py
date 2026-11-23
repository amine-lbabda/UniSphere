
from django.contrib import admin

from .models import (
    Group,
    GroupMember,
    GroupInvitation,
    TeamContract,
    ContractAcceptance,
    Project,
    ProjectRole,
    ProjectMember,
    Task,
    TaskAssignment,
    Meeting,
    MeetingAttendance,
    MeetingMinutes,
    Decision,
    ContributionEvaluation,
)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'created_by',
        'status',
        'max_members',
        'active_members',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
        'created_by__username',
    )

    readonly_fields = (
        'created_at',
    )

    ordering = ('-created_at',)

    @admin.display(description='Active Members')
    def active_members(self, obj):
        return f"{obj.get_active_members_count()} / {obj.max_members}"

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'group',
        'role',
        'status',
        'joined_at',
    )

    list_filter = (
        'role',
        'status',
        'group',
    )

    search_fields = (
        'user__username',
        'group__name',
    )

    readonly_fields = (
        'joined_at',
    )

    list_select_related = (
        'user',
        'group',
    )

    ordering = ('group__name', 'role')

@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):

    list_display = (
        'group',
        'invited_user',
        'invited_by',
        'status',
        'created_at',
        'responded_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'group__name',
        'invited_user__username',
        'invited_by__username',
    )

    readonly_fields = (
        'created_at',
        'responded_at',
    )

    list_select_related = (
        'group',
        'invited_user',
        'invited_by',
    )

    ordering = ('-created_at',)

@admin.register(TeamContract)
class TeamContractAdmin(admin.ModelAdmin):

    list_display = (
        'group',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'group__name',
        'rules',
        'objectives',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    list_select_related = ('group',)

    ordering = ('-created_at',)

    fieldsets = (
        ('Group Information', {
            'fields': ('group',)
        }),
        ('Team Rules', {
            'fields': ('rules',)
        }),
        ('Project Objectives', {
            'fields': ('objectives',)
        }),
        ('Contract History', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(ContractAcceptance)
class ContractAcceptanceAdmin(admin.ModelAdmin):

    list_display = (
        'member_name',
        'group_name',
        'accepted',
        'accepted_at',
    )

    list_filter = (
        'accepted',
        'contract__group',
    )

    search_fields = (
        'member__user__username',
        'contract__group__name',
    )

    readonly_fields = ('accepted_at',)

    list_select_related = (
        'member__user',
        'contract__group',
    )

    @admin.display(description='Member')
    def member_name(self, obj):
        return obj.member.user

    @admin.display(description='Group')
    def group_name(self, obj):
        return obj.contract.group.name

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'group',
        'status',
        'start_date',
        'deadline',
        'project_progress',
    )

    list_filter = (
        'status',
        'start_date',
        'deadline',
    )

    search_fields = (
        'title',
        'description',
        'group__name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'project_progress',
    )

    list_select_related = ('group',)

    ordering = ('-created_at',)

    fieldsets = (
        ('Project Information', {
            'fields': ('title', 'description', 'group')
        }),
        ('Project Timeline', {
            'fields': ('start_date', 'deadline')
        }),
        ('Project Status', {
            'fields': ('status', 'project_progress')
        }),
        ('History', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Progress')
    def project_progress(self, obj):
        from collaboration.services.project_progress_service import (
            calculate_project_progress
        )
        return f"{calculate_project_progress(obj)}%"

@admin.register(ProjectRole)
class ProjectRoleAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'project',
        'description_preview',
    )

    list_filter = (
        'project',
    )

    search_fields = (
        'name',
        'description',
        'project__title',
    )

    list_select_related = ('project',)

    ordering = ('project__title', 'name')

    @admin.display(description='Description')
    def description_preview(self, obj):
        if not obj.description:
            return "No description"
        return (
            obj.description[:60] + "..."
            if len(obj.description) > 60
            else obj.description
        )

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):

    list_display = (
        'member_name',
        'project',
        'role',
        'group_name',
        'assigned_at',
    )

    list_filter = (
        'project',
        'role',
        'group_member__group',
    )

    search_fields = (
        'group_member__user__username',
        'project__title',
        'role__name',
        'group_member__group__name',
    )

    readonly_fields = ('assigned_at',)

    list_select_related = (
        'project',
        'role',
        'group_member__user',
        'group_member__group',
    )

    ordering = ('project__title', 'role__name')

    @admin.display(description='Member')
    def member_name(self, obj):
        return obj.group_member.user

    @admin.display(description='Group')
    def group_name(self, obj):
        return obj.group_member.group.name

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'project',
        'status',
        'priority',
        'start_date',
        'deadline',
        'estimated_hours',
        'created_by',
    )

    list_filter = (
        'status',
        'priority',
        'project',
        'deadline',
    )

    search_fields = (
        'title',
        'description',
        'project__title',
        'created_by__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    list_select_related = (
        'project',
        'created_by',
    )

    ordering = ('deadline',)

    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'project')
        }),
        ('Task Progress', {
            'fields': ('status', 'priority')
        }),
        ('Task Schedule', {
            'fields': (
                'start_date',
                'deadline',
                'estimated_hours',
            )
        }),
        ('Creation Information', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        'task',
        'member_name',
        'project_name',
        'assigned_at',
    )

    list_filter = (
        'task__project',
        'assigned_at',
    )

    search_fields = (
        'task__title',
        'project_member__group_member__user__username',
        'task__project__title',
    )

    readonly_fields = ('assigned_at',)

    list_select_related = (
        'task__project',
        'project_member__group_member__user',
    )

    ordering = ('task__deadline',)

    @admin.display(description='Assigned Member')
    def member_name(self, obj):
        return obj.project_member.group_member.user

    @admin.display(description='Project')
    def project_name(self, obj):
        return obj.task.project.title
@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'project',
        'date',
        'start_time',
        'end_time',
        'organizer',
        'status',
    )

    list_filter = (
        'status',
        'date',
        'project',
    )

    search_fields = (
        'title',
        'description',
        'project__title',
        'organizer__username',
    )

    readonly_fields = ('created_at',)

    list_select_related = (
        'project',
        'organizer',
    )

    ordering = ('-date', '-start_time')

    fieldsets = (
        ('Meeting Information', {
            'fields': ('title', 'description', 'project')
        }),
        ('Meeting Schedule', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Meeting Location', {
            'fields': ('location', 'meeting_link')
        }),
        ('Organization', {
            'fields': ('organizer', 'status')
        }),
        ('History', {
            'fields': ('created_at',)
        }),
    )
@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'meeting',
        'member_name',
        'member_group',
        'status',
        'responded_at',
    )

    list_filter = (
        'status',
        'meeting__date',
        'meeting__project',
    )

    search_fields = (
        'meeting__title',
        'group_member__user__username',
        'group_member__group__name',
    )

    readonly_fields = ('responded_at',)

    list_select_related = (
        'meeting',
        'meeting__project',
        'group_member',
        'group_member__user',
        'group_member__group',
    )

    ordering = ('meeting__date', 'meeting__start_time')

    @admin.display(description='Member')
    def member_name(self, obj):
        return obj.group_member.user

    @admin.display(description='Group')
    def member_group(self, obj):
        return obj.group_member.group.name

@admin.register(MeetingMinutes)
class MeetingMinutesAdmin(admin.ModelAdmin):

    list_display = (
        'meeting',
        'created_by',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'created_at',
        'updated_at',
    )

    search_fields = (
        'meeting__title',
        'discussion_summary',
        'decisions',
        'action_items',
        'created_by__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    list_select_related = (
        'meeting',
        'created_by',
    )

    ordering = ('-created_at',)

    fieldsets = (
        ('Meeting Information', {
            'fields': ('meeting', 'created_by')
        }),
        ('Discussion Summary', {
            'fields': ('discussion_summary',)
        }),
        ('Decisions', {
            'fields': ('decisions',)
        }),
        ('Action Items', {
            'fields': ('action_items',)
        }),
        ('History', {
            'fields': ('created_at', 'updated_at')
        }),
    )
@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'meeting',
        'responsible_member_name',
        'deadline',
        'status',
        'created_by',
    )

    list_filter = (
        'status',
        'deadline',
        'meeting',
    )

    search_fields = (
        'title',
        'description',
        'meeting__title',
        'responsible_member__user__username',
        'created_by__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    list_select_related = (
        'meeting',
        'responsible_member__user',
        'created_by',
    )

    ordering = ('deadline', '-created_at')

    fieldsets = (
        ('Decision Information', {
            'fields': ('meeting', 'title', 'description')
        }),
        ('Responsibility', {
            'fields': ('responsible_member', 'deadline')
        }),
        ('Progress', {
            'fields': ('status',)
        }),
        ('Creation Information', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    @admin.display(description='Responsible Member')
    def responsible_member_name(self, obj):
        if obj.responsible_member:
            return obj.responsible_member.user
        return "Not assigned"
@admin.register(ContributionEvaluation)
class ContributionEvaluationAdmin(admin.ModelAdmin):

    list_display = (
        'member_name',
        'project',
        'evaluated_by',
        'task_completion_score',
        'work_quality_score',
        'collaboration_score',
        'deadline_respect_score',
        'overall_score_display',
        'created_at',
    )

    list_filter = (
        'project',
        'created_at',
    )

    search_fields = (
        'project__title',
        'project_member__group_member__user__username',
        'evaluated_by__username',
        'feedback',
    )

    readonly_fields = (
        'overall_score_display',
        'created_at',
        'updated_at',
    )

    list_select_related = (
        'project',
        'project_member__group_member__user',
        'evaluated_by',
    )

    ordering = ('-created_at',)

    fieldsets = (
        ('Evaluation Information', {
            'fields': ('project', 'project_member', 'evaluated_by')
        }),
        ('Performance Scores', {
            'fields': (
                'task_completion_score',
                'work_quality_score',
                'collaboration_score',
                'deadline_respect_score',
                'overall_score_display',
            )
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
        ('History', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Member')
    def member_name(self, obj):
        return obj.project_member.group_member.user

    @admin.display(description='Overall Score')
    def overall_score_display(self, obj):
        return f"{obj.overall_score}/5"