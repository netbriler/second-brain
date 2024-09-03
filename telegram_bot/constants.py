from enum import Enum

from django.utils.translation import gettext_lazy as _


class FileContentType(str, Enum):
    AUDIO = 'audio'
    DOCUMENT = 'document'
    PHOTO = 'photo'
    STORY = 'story'
    VIDEO = 'video'
    VIDEO_NOTE = 'video_note'
    VOICE = 'voice'
    LOCATION = 'location'


FILE_CONTENT_TYPES = (
    (FileContentType.AUDIO.value, 'audio'),
    (FileContentType.DOCUMENT.value, 'document'),
    (FileContentType.PHOTO.value, 'photo'),
    (FileContentType.STORY.value, 'story'),
    (FileContentType.VIDEO.value, 'video'),
    (FileContentType.VIDEO_NOTE.value, 'video_note'),
    (FileContentType.VOICE.value, 'voice'),
    (FileContentType.LOCATION.value, 'location'),
)


class MessageRoles(Enum):
    SIMPLE = 'simple', _('Simple')
    VOICE_RECOGNITION = 'voice_recognition', _('Voice Recognition')
    TEXT_RECOGNITION = 'text_recognition', _('Text Recognition')

    @property
    def label(self):
        return self.value[1]
