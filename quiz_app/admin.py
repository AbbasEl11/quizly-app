from django.contrib import admin
from quiz_app.models import Quiz, Question


class QuestionInline(admin.TabularInline):
    """Inline admin interface for Questions within Quiz admin."""
    model = Question
    extra = 1
    fields = ('question_title', 'question_options', 'answer')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin interface for Quiz model with inline Questions."""
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'user')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [QuestionInline]
    
    fieldsets = (
        ('Quiz Information', {
            'fields': ('user', 'title', 'description', 'video_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for Question model."""
    list_display = ('question_title', 'quiz', 'created_at')
    list_filter = ('quiz', 'created_at')
    search_fields = ('question_title', 'quiz__title')
    readonly_fields = ('created_at', 'updated_at')
