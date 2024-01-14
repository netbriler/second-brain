from enum import Enum


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
