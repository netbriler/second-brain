from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from djangoql.admin import DjangoQLSearchMixin

from ai.tasks import send_file_to_user_task, transcribe_file_task

from . import models
from .constants import FileContentType


@admin.register(models.File)
class CourseAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    list_select_related = ('uploaded_by',)

    search_fields = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    list_filter = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    readonly_fields = (
        'id',
        'content_type',
        'title',
        'file_id',
        'thumbnail_id',
        'raw_data',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'id',
                    'content_type',
                    'title',
                    'file_id',
                    'thumbnail_id',
                    'raw_data',
                    'created_at',
                    'updated_at',
                    'uploaded_by',
                ],
            },
        ),
    ]

    actions = [
        'send_to_telegram',
        'transcribe_audio_to_text',
    ]

    @admin.action(description=_('Send to telegram'))
    def send_to_telegram(self, request, queryset):
        for file in queryset:
            send_file_to_user_task.delay(file.id, request.user.id)

        self.message_user(request, _('Files sent to telegram'))

    @admin.action(description=_('Transcribe audio to text'))
    def transcribe_audio_to_text(self, request, queryset):
        for file in queryset:
            if file.content_type not in [FileContentType.VOICE.value, FileContentType.AUDIO.value]:
                self.message_user(request, _('Only audio files are supported for transcription'))
                return

            if not file.raw_data.get('mime_type', None):
                self.message_user(request, _('File {file_id} is not an audio file').format(file_id=file.file_id))
                continue

            transcribe_file_task.delay(
                chat_id=request.user.telegram_id,
                file_id=file.id,
                user_id=request.user.id,
                message_id=None,
            )

        self.message_user(request, _('Files sent to transcription'))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
