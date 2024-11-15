import os

from django.conf import settings
from telethon import TelegramClient
from telethon.sessions import StringSession, MemorySession
from telethon.tl.types import MessageActionTopicCreate

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

    async def get_client(self, account: Account = None, bot_token: str = None, key: str = 'client'):
        if not self.clients.get(key):
            if account:
                self.clients[key] = TelegramClient(
                    StringSession(
                        account.session_string
                    ), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
                )
            if bot_token:
                self.clients[key] = TelegramClient(
                    MemorySession(), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
                )

        if account:
            await self.clients[key].connect()
        elif bot_token:
            await self.clients[key].start(bot_token=bot_token)

        return self.clients[key]

    async def get_channel(self, client, channel_id):
        if not self.channels.get(channel_id):
            self.channels[channel_id] = await client.get_entity(channel_id)

        return self.channels[channel_id]

    async def get_chapter(self, client, channel_id, chapter_id):
        if not self.chapters.get(chapter_id):
            self.chapters[chapter_id] = \
                (await client.get_messages(await self.get_channel(channel_id), ids=[chapter_id]))[0]
        return self.chapters[chapter_id]

    async def get_message(self, client, channel_id, message_id):
        if not self.messages.get(message_id):
            self.messages[message_id] = \
                (await client.get_messages(await self.get_channel(channel_id), ids=[message_id]))[0]
        return self.messages[message_id]

    async def prepare(self, process: Process, job: Job):
        """
        Creates jobs to download data from telegram channel
        The next stages: send_ethers_batch, send_ethers, send_tokens
        """
        data = job.data

        from_account_id = data.get('from_account_id')
        if not from_account_id:
            return await self.fail_process(process, job, f'from_account_id is required.')

        try:
            from_account = await Account.objects.aget(id=from_account_id)
        except Account.DoesNotExist:
            return self.fail_process(process, job, f'From account not found.')

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

        try:
            bot = await self.get_client(bot_token=settings.TELEGRAM_BOT_TOKEN, key='bot')

            me = await bot.get_me()
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to initialize bot.')

        if not me:
            return await self.fail_process(process, job, f'Failed to get bot.')

        try:
            entity = await bot.get_entity(destination_user_id)
            await self.job_log(job, f'Checked destination user: {entity}')
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to get entity.')

        channel_id = data.get('channel_id')
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
                channel, ids=data.get('chapter_ids', []) + data.get('message_ids', []),
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
            self.chapters[chapter.id] = chapter
            async for message in client.iter_messages(channel, reply_to=chapter.id, reverse=True):
                parents = [job]
                if last_job != job:
                    parents.append(last_job)

                data = {
                    'channel_id': channel.id,
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

                self.messages[message.id] = message

        for message in messages:
            self.messages[message.id] = message
            parents = [job]
            if last_job != job:
                parents.append(last_job)

            data = {
                'channel_id': channel.id,
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

        if not data.get('chapter_ids', []) + data.get('message_ids', []):
            async for message in client.iter_messages(channel, reverse=True):
                parents = [job]
                if last_job != job:
                    parents.append(last_job)

                data = {
                    'channel_id': channel.id,
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

                self.messages[message.id] = message

        # finish prepare job, this will activate next jobs
        await self.done_job(job)

    async def progress_callback(self, job, current=0, total=0):
        if not total:
            total = 0
        stats = ProgressTracker().callback(current, total)
        await self.job_log(job, f'{stats}')

    async def download_media(self, process: Process, job: Job):
        client = await self.get_client(await Account.objects.aget(id=process.data['from_account_id']))

        message = await self.get_message(client, job.data['channel_id'], job.data['message_id'])
        if not message.document:
            return await self.fail_job(job, 'Message has no document.')

        file = await client.download_file(
            message.document, f'./downloads/{message.document.id}.mp4',
            progress_callback=lambda current, total: self.progress_callback(job, current, total),
        )
        await self.job_log(job, f'File downloaded: {file}')
        await self.done_job(job)

    async def send_message(self, process: Process, job: Job):
        client = await self.get_client(await Account.objects.aget(id=process.data['from_account_id']))
        bot = await self.get_client(bot_token=settings.TELEGRAM_BOT_TOKEN, key='bot')
        entity = await bot.get_entity(process.data.get('destination_user_id'))

        message = await self.get_message(
            client, job.data['channel_id'], job.data['message_id']
        )
        text = message.text or ''
        if message.action and isinstance(message.action, MessageActionTopicCreate):
            text = message.action.title

        file_path = None
        if message.document:
            extension = ''
            if message.document.mime_type and len(message.document.mime_type.split('/')) > 1:
                extension = '.' + message.document.mime_type.split('/')[1]
            file_path = f'./downloads/{message.document.id}' + extension
            await bot.send_file(
                entity, file_path,
                progress_callback=lambda current, total: self.progress_callback(job, current, total),
                caption=text[:1024],
            )

            text = text[1024:]

        text_size = 4096
        if text:
            for i in range(0, len(text), text_size):
                await bot.send_message(entity, text[i:i + text_size])

        await self.done_job(job)

        if file_path:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                else:
                    raise FileNotFoundError(f'File not found: {file_path}')
            except Exception as e:
                await self.process_log(process, str(e))
