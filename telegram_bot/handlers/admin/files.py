import re
from typing import NoReturn

from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import Command, CommandObject, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReactionTypeEmoji
from django.utils.translation import gettext as _

from courses.models import Lesson
from telegram_bot.filters.admin import IsAdmin
from telegram_bot.filters.i18n_text import I18nText
from telegram_bot.keyboards.default.cancel import get_cancel_markup
from telegram_bot.models import File
from telegram_bot.services.courses import create_lesson_entity_from_file
from telegram_bot.services.files import generate_file_text, save_file, send_file_to_user
from telegram_bot.states.file import FilesAddForm, LessonFilesAddForm
from users.models import User

router = Router(name=__name__)


@router.message(
    IsAdmin(),
    Command(commands=['file']),
    F.reply_to_message.content_type.in_(
        {
            ContentType.AUDIO,
            ContentType.DOCUMENT,
            ContentType.PHOTO,
            ContentType.STICKER,
            ContentType.VIDEO,
            ContentType.VIDEO_NOTE,
            ContentType.VOICE,
        },
    ),
)
async def _file_reply(message: Message, user: User) -> NoReturn:
    """Save file from reply and return file info"""
    file = await save_file(
        message=message.reply_to_message,
        user=user,
    )

    if file:
        file = await File.objects.filter(file_id__iexact=file.file_id).select_related('uploaded_by').afirst()
        file_text = generate_file_text(file)
        await message.answer(file_text)
    else:
        await message.answer(_('Failed to save file'))


@router.message(
    IsAdmin(),
    Command(re.compile(r'file[\s|_]?([\w]*)', re.IGNORECASE)),
)
async def _file(message: Message, bot: Bot, command: CommandObject, user: User) -> NoReturn:
    search_file = command.regexp_match.group(1) or command.args
    if not search_file:
        return await message.answer(_('Usage:\n/file [file_id]'))

    file = await File.objects.filter(file_id__iexact=search_file).select_related('uploaded_by').afirst()

    if not file:
        await message.answer(_('file not found'))
        return NoReturn

    await send_file_to_user(bot, file, user, send_file_info=True)


@router.message(
    IsAdmin(),
    or_f(
        I18nText('Upload file 📁'),
        Command(commands=['upload_files']),
    ),
)
async def _upload_files(message: Message, state: FSMContext) -> NoReturn:
    await state.set_state(FilesAddForm.add_file)

    await message.answer(_('Send me a something to upload'), reply_markup=get_cancel_markup())


@router.message(
    IsAdmin(),
    FilesAddForm.add_file,
    F.content_type.in_(
        {
            ContentType.AUDIO,
            ContentType.DOCUMENT,
            ContentType.PHOTO,
            ContentType.STICKER,
            ContentType.VIDEO,
            ContentType.VIDEO_NOTE,
            ContentType.VOICE,
        },
    ),
)
async def _upload_file(message: Message, user: User, bot: Bot) -> NoReturn:
    await message.react([ReactionTypeEmoji(emoji='👀')])
    await save_file(
        message=message,
        user=user,
    )
    await message.react([ReactionTypeEmoji(emoji='👍')])


@router.message(
    IsAdmin(),
    Command(re.compile(r'lesson_upload_files[\s|_]?([\w]*)', re.IGNORECASE)),
)
async def _lesson_upload_files(message: Message, state: FSMContext, command: CommandObject) -> NoReturn:
    lesson_id = command.regexp_match.group(1) or command.args
    if not lesson_id:
        return await message.answer(_('Usage:\n/lesson_upload_files [lesson_id]'))

    try:
        lesson_id = int(lesson_id)
    except ValueError:
        return await message.answer(_('Invalid lesson_id. Must be a number.'))

    lesson = await Lesson.objects.filter(id=lesson_id).afirst()
    if not lesson:
        return await message.answer(_('Lesson not found'))

    await state.update_data(lesson_id=lesson_id)
    await state.set_state(LessonFilesAddForm.add_file)

    await message.answer(
        _('Send me files to upload for lesson: {lesson_title}').format(lesson_title=lesson.title),
        reply_markup=get_cancel_markup(),
    )


@router.message(
    IsAdmin(),
    LessonFilesAddForm.add_file,
    F.content_type.in_(
        {
            ContentType.AUDIO,
            ContentType.DOCUMENT,
            ContentType.PHOTO,
            ContentType.STICKER,
            ContentType.VIDEO,
            ContentType.VIDEO_NOTE,
            ContentType.VOICE,
        },
    ),
)
async def _lesson_upload_file(message: Message, user: User, state: FSMContext) -> NoReturn:
    await message.react([ReactionTypeEmoji(emoji='👀')])

    data = await state.get_data()
    lesson_id = data.get('lesson_id')

    lesson = await Lesson.objects.filter(id=lesson_id).afirst()
    if not lesson:
        await message.answer(_('Lesson not found'))
        await state.clear()
        return NoReturn

    file = await save_file(
        message=message,
        user=user,
    )

    if file:
        await create_lesson_entity_from_file(lesson=lesson, file=file)
        await message.react([ReactionTypeEmoji(emoji='👍')])
    else:
        await message.react([ReactionTypeEmoji(emoji='👎')])
        await message.answer(_('Failed to save file'))
