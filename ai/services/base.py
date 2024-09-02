from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from pydantic import BaseModel

from ai.models import Message
from users.models import User


class AIResponse(BaseModel):
    text: str | None = None
    prompt: str | None = None
    response: str | None = None
    category: str | None = None
    time_spent: float | None = None
    error_message: str | None = None
    is_successful: bool = True


class TextRecognition(BaseModel):
    text: str | None = None
    category_predictions: list[str] | None = None


class TextRecognitionResponse(AIResponse):
    text_recognition: TextRecognition | None = None


class VoiceRecognitionResponse(AIResponse):
    text_recognition: str | None = None


def save_ai_response(response: AIResponse, source: Model = None, requested_by: User = None) -> Message:
    source_type = None
    source_id = None
    if source:
        source_type = ContentType.objects.get_for_model(source)
        source_id = source.pk

    message = Message.objects.create(
        text=response.text,
        prompt=response.prompt,
        response=response.response,
        category=response.category,
        time_spent=response.time_spent,
        source_id=source_id,
        source_type=source_type,
        requested_by=requested_by,
    )

    return message
