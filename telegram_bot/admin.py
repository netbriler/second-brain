from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.html import format_html
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
        'short_file_id',
        'short_file_unique_id',
        'mime_type',
        'uploaded_by_link',
        'created_at',
        'updated_at',
    )

    list_select_related = ('uploaded_by',)

    search_fields = (
        'id',
        'content_type',
        'file_id',
        'file_unique_id',
        'mime_type',
        'created_at',
        'updated_at',
        'uploaded_by',
    )

    list_filter = (
        'content_type',
        'created_at',
        'updated_at',
        'uploaded_by',
        AutocompleteFilterFactory(_('Uploaded By'), 'uploaded_by'),
    )

    list_display_links = ('id', 'content_type', 'short_file_id', 'short_file_unique_id')

    readonly_fields = (
        'id',
        'content_type',
        'file_id',
        'file_unique_id',
        'mime_type',
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
                    'file_id',
                    'file_unique_id',
                    'mime_type',
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

    # add title translation here
    def short_file_id(self, obj):
        return obj.file_id[:10] + '...' if obj.file_id else ''

    short_file_id.short_description = _('Short File ID')

    def short_file_unique_id(self, obj):
        return obj.file_unique_id[:10] + '...' if obj.file_unique_id else ''

    short_file_unique_id.short_description = _('Short File Unique ID')

    def uploaded_by_link(self, obj):
        if obj.uploaded_by:
            url = reverse(
                f'admin:{obj.uploaded_by._meta.app_label}_{obj.uploaded_by._meta.model_name}_change',  # noqa: SLF001
                args=[obj.uploaded_by.pk],
            )
            return format_html(
                '<a href="{url}">{text}</a>',
                url=url,
                text=str(obj.uploaded_by),
            )

    uploaded_by_link.short_description = _('Uploaded By')

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

            if not file.mime_type:
                self.message_user(request, _('File {file_id} is not an audio file').format(file_id=file.file_id))
                continue

            transcribe_file_task.delay(
                chat_id=request.user.telegram_id,
                file_id=file.id,
                user_id=request.user.id,
                message_id=None,
                source_id=file.id,
                source_type_id=ContentType.objects.get_for_model(models.File).id,
            )

        self.message_user(request, _('Files sent to transcription'))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Message)
class MessageAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    list_display = (
        'message_id',
        'chat_id',
        'text',
        'user_link',
        'file_link',
        'role',
        'created_at',
        'updated_at',
    )

    list_select_related = ('user', 'file')

    list_display_links = ('message_id', 'chat_id', 'text')

    search_fields = (
        'message_id',
        'chat_id',
        'text',
        'file',
        'user',
        'role',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'created_at',
        'updated_at',
        'user',
        'file',
        'role',
        AutocompleteFilterFactory(_('User'), 'user'),
        AutocompleteFilterFactory(_('File'), 'file'),
    )

    readonly_fields = (
        'message_id',
        'chat_id',
        'text',
        'file',
        'user',
        'role',
        'raw_data',
        'created_at',
        'updated_at',
    )

    fieldsets = [
        (
            _('General'),
            {
                'fields': [
                    'message_id',
                    'chat_id',
                    'text',
                    'file',
                    'user',
                    'role',
                    'raw_data',
                    'created_at',
                    'updated_at',
                ],
            },
        ),
    ]

    def user_link(self, obj):
        if obj.user:
            url = reverse(
                f'admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change',  # noqa: SLF001
                args=[obj.user.pk],
            )
            return format_html(
                '<a href="{url}">{text}</a>',
                url=url,
                text=str(obj.user),
            )

    user_link.short_description = _('User')

    def file_link(self, obj):
        if obj.file:
            url = reverse(
                f'admin:{obj.file._meta.app_label}_{obj.file._meta.model_name}_change',  # noqa: SLF001
                args=[obj.file.pk],
            )
            return format_html(
                '<a href="{url}">{text}</a>',
                url=url,
                text=str(obj.file),
            )

    file_link.short_description = _('File')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
