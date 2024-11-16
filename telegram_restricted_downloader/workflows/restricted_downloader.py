from pathlib import Path

from django.conf import settings
from telethon import TelegramClient
from telethon.errors import AuthKeyUnregisteredError
from telethon.sessions import StringSession, MemorySession
from telethon.tl.types import MessageActionTopicCreate, DocumentAttributeAudio, DocumentAttributeVideo

from telegram_bot.services.restricted_downloader import fetch_channel_info, get_topic_text, get_message_text
from telegram_restricted_downloader.helpers import ProgressTracker
from telegram_restricted_downloader.models import Account
from workflows.constants import JOB_PLANNED
from workflows.models import Process, Job
from workflows.workflow import AsyncWorkflow


class RestrictedDownloaderWorkflow(AsyncWorkflow):
    def __init__(self):
        super().__init__()
        self.clients = dict()
        self.channels = dict()
        self.messages = dict()
        self.chapters = dict()

    async def get_client(
            self,
            account: Account = None,
            bot_token: str = settings.TELEGRAM_BOT_TOKEN,
            key: str = 'client'
    ):
        if not self.clients.get(key):
            if account:
                self.clients[key] = TelegramClient(
                    StringSession(
                        account.session_string
                    ), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
                )
            elif bot_token:
                self.clients[key] = TelegramClient(
                    MemorySession(), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
                )

        if account:
            await self.clients[key].connect()
        elif bot_token:
            await self.clients[key].start(bot_token=bot_token)

        return self.clients[key]

    async def get_channel(self, client, channel_id: int):
        channel_id = int(channel_id)
        if not self.channels.get(channel_id):
            self.channels[channel_id] = await client.get_entity(channel_id)

        return self.channels[channel_id]

    async def get_chapter(self, client, channel_id: int, chapter_id: int):
        channel_id = int(channel_id)
        chapter_id = int(chapter_id)
        if not self.chapters.get(chapter_id):
            self.chapters[chapter_id] = \
                (await client.get_messages(await self.get_channel(client, channel_id), ids=[chapter_id]))[0]
        return self.chapters[chapter_id]

    async def get_message(self, client, channel_id: int, message_id: int):
        channel_id = int(channel_id)
        message_id = int(message_id)
        if not self.messages.get(message_id):
            self.messages[message_id] = \
                (await client.get_messages(await self.get_channel(client, channel_id), ids=[message_id]))[0]
        return self.messages[message_id]

    async def prepare(self, process: Process, job: Job):
        """
        Creates jobs to download data from telegram channel
        The next stages: send_ethers_batch, send_ethers, send_tokens
        """
        from_account_id = job.data.get('from_account_id')
        if not from_account_id:
            return await self.fail_process(process, job, f'from_account_id is required.')

        try:
            from_account = await Account.objects.aget(id=from_account_id)
        except Account.DoesNotExist:
            return await self.fail_process(process, job, f'From account not found.')

        try:
            client = await self.get_client(from_account)

            me = await client.get_me()
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to initialize client.')

        if not me:
            return await self.fail_process(process, job, f'Failed to get client.')

        destination_user_id = job.data.get('destination_user_id')
        if not destination_user_id:
            return await self.fail_process(process, job, f'Destination user id is required.')

        sender_account = None
        if process.data.get('sender_account_id'):
            try:
                sender_account = await Account.objects.aget(id=process.data.get('sender_account_id'))
            except Account.DoesNotExist:
                sender_account = None

        try:
            sender = await self.get_client(sender_account, key='sender')

            me = await sender.get_me()
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to initialize sender.')

        if not me:
            return await self.fail_process(process, job, f'Failed to get sender.')

        try:
            entity = await sender.get_entity(destination_user_id)
            await self.job_log(job, f'Checked destination user: {entity}')
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to get entity.')

        channel_id = job.data.get('channel_id')
        if not channel_id:
            return await self.fail_process(process, job, f'Channel id is required.')

        try:
            channel, text = await fetch_channel_info(client, channel_id)
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to get channel.')

        await self.process_log(process, f'RestrictedDownloaderWorkflow.prepare: {text}')

        messages = []
        chapters = []
        async for message in client.iter_messages(
                channel, ids=job.data.get('chapter_ids', []) + job.data.get('message_ids', []),
                reverse=True,
        ):
            if isinstance(message.action, MessageActionTopicCreate):
                await self.job_log(job, f'Message {message.id} is a topic: {get_topic_text(message)}')
                chapters.append(message)
            else:
                await self.job_log(job, f'Message {message.id} is a message: {get_message_text(message)}')
                messages.append(message)
        last_job = job
        for chapter in chapters:
            self.chapters[int(chapter.id)] = chapter
            async for message in client.iter_messages(channel, reply_to=chapter.id, reverse=True):
                parents = [job]
                if last_job != job:
                    parents.append(last_job)

                data = {
                    'channel_id': channel_id,
                    'chapter_id': chapter.id,
                    'message_id': message.id,
                }
                if message.document:
                    last_job = await self.create_job(
                        stage='download_media',
                        process=process,
                        parents=parents,
                        data=data,
                        status=JOB_PLANNED,
                    )
                    parents.append(last_job)
                last_job = await self.create_job(
                    stage='send_message',
                    process=process,
                    parents=parents,
                    data=data,
                    status=JOB_PLANNED,
                )

                self.messages[int(message.id)] = message

        for message in messages:
            self.messages[int(message.id)] = message
            parents = [job]
            if last_job != job:
                parents.append(last_job)

            data = {
                'channel_id': channel_id,
                'message_id': message.id,
            }
            if message.document:
                last_job = await self.create_job(
                    stage='download_media',
                    process=process,
                    parents=parents,
                    data=data,
                    status=JOB_PLANNED,
                )
                parents.append(last_job)
            last_job = await self.create_job(
                stage='send_message',
                process=process,
                parents=parents,
                data=data,
                status=JOB_PLANNED,
            )

        if not job.data.get('chapter_ids', []) + job.data.get('message_ids', []):
            async for message in client.iter_messages(channel, reverse=True):
                parents = [job]
                if last_job != job:
                    parents.append(last_job)

                data = {
                    'channel_id': channel_id,
                    'message_id': message.id,
                }
                if message.document:
                    last_job = await self.create_job(
                        stage='download_media',
                        process=process,
                        parents=parents,
                        data=data,
                        status=JOB_PLANNED,
                    )
                    parents.append(last_job)
                last_job = await self.create_job(
                    stage='send_message',
                    process=process,
                    parents=parents,
                    data=data,
                    status=JOB_PLANNED,
                )

                self.messages[int(message.id)] = message

        # finish prepare job, this will activate next jobs
        await self.done_job(job)

    async def progress_callback(self, job, current=0, total=0):
        if not total:
            total = 0
        stats = ProgressTracker().callback(current, total)
        await self.update_job_data(job, {'progress': stats})

    async def download_media(self, process: Process, job: Job):
        client = await self.get_client(await Account.objects.aget(id=process.data['from_account_id']))

        try:
            message = await self.get_message(client, job.data['channel_id'], job.data['message_id'])
        except AuthKeyUnregisteredError:
            return await self.fail_job(job, 'Source client session is invalid.')
        except Exception as e:
            if 'Could not find the input entity' in str(e):
                return await self.fail_job(
                    job, 'Channel not found.' if 'PeerChannel' in str(e) else 'Message not found.'
                )
            elif 'The key is not registered in the system' in str(e):
                return await self.fail_job(job, 'Source client session is invalid.')
            raise
        if not message.document:
            return await self.fail_job(job, 'Message has no document.')

        extension = ''
        if message.document.mime_type and len(message.document.mime_type.split('/')) > 1:
            extension = '.' + message.document.mime_type.split('/')[1]
        file_path = f'./downloads/{message.document.id}' + extension

        file = await client.download_file(
            message.document, file_path,
            progress_callback=lambda current, total: self.progress_callback(job, current, total),
        )
        await self.job_log(job, f'File downloaded: {file}')
        await self.done_job(job)

    def detect_document_kwargs(self, document):
        kwargs = {}
        if document.mime_type and len(document.mime_type.split('/')) > 1 and document.attributes:
            _type, exception = document.mime_type.split('/')

            if _type == 'audio' and document.attributes:
                for attribute in document.attributes:
                    if isinstance(attribute, DocumentAttributeAudio):
                        kwargs['voice_note'] = attribute.voice
                        break

            elif _type == 'video' and document.attributes:
                for attribute in document.attributes:
                    if isinstance(attribute, DocumentAttributeVideo):
                        kwargs['video_note'] = attribute.round_message
                        break

        return kwargs

    async def send_message(self, process: Process, job: Job):
        client = await self.get_client(await Account.objects.aget(id=process.data['from_account_id']))
        sender_account = None
        if process.data.get('sender_account_id'):
            try:
                sender_account = await Account.objects.aget(id=process.data.get('sender_account_id'))
            except Account.DoesNotExist:
                sender_account = None

        sender = await self.get_client(sender_account, key='sender')
        destination_user = await sender.get_entity(process.data.get('destination_user_id'))

        try:
            message = await self.get_message(
                client, job.data['channel_id'], job.data['message_id']
            )
        except AuthKeyUnregisteredError:
            return await self.fail_job(job, 'Source client session is invalid.')
        except Exception as e:
            if 'Could not find the input entity' in str(e):
                return await self.fail_job(job, 'Channel not found.' if 'PeerChannel' in str(e) else 'Message not found.')
            elif 'The key is not registered in the system' in str(e):
                return await self.fail_job(job, 'Source client session is invalid.')
            raise
        text = message.message or ''
        if message.action and isinstance(message.action, MessageActionTopicCreate):
            text = message.action.title

        try:
            sent_message = None
            file_path = None
            if message.document:
                extension = ''
                if message.document.mime_type and len(message.document.mime_type.split('/')) > 1:
                    extension = '.' + message.document.mime_type.split('/')[1]
                file_path = f'./downloads/{message.document.id}' + extension
                sent_message = await sender.send_file(
                    destination_user, file_path,
                    progress_callback=lambda current, total: self.progress_callback(job, current, total),
                    caption=text[:1024],
                    formatting_entities=message.entities,
                    **self.detect_document_kwargs(message.document)
                )

                text = text[1024:]

            text_size = 4096
            if text:
                for i in range(0, len(text), text_size):
                    m1 = await sender.send_message(
                        destination_user, text[i:i + text_size],
                        formatting_entities=message.entities if i == 0 else None,
                        reply_to=sent_message,
                    )
                    if not sent_message:
                        sent_message = m1

        except AuthKeyUnregisteredError:
            return await self.fail_job(job, 'Sender client session is invalid.')
        except Exception as e:
            if 'The key is not registered in the system' in str(e):
                return await self.fail_job(job, 'Sender client session is invalid.')
            raise

        await self.done_job(job)

        if file_path:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                else:
                    raise FileNotFoundError(f'File not found: {file_path}')
            except Exception as e:
                await self.process_log(process, str(e))
