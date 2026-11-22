from django.contrib import admin

# Register your models here.

from .models import Idea


@admin.register(Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'author', 'content_preview', 'status', 'created_at')
    list_filter = ('type', 'status')
    search_fields = ('title', 'content', 'author__username')

    @admin.display(description='Contenu')
    def content_preview(self, obj):
        return obj.content[:80] + ('...' if len(obj.content) > 80 else '')