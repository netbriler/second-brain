from django.conf import settings
from telethon import TelegramClient
from telethon.sessions import StringSession

from telegram_bot.services.restricted_downloader import fetch_channel_info
from telegram_restricted_downloader.models import Account
from workflows.models import Process, Job
from workflows.workflow import AsyncWorkflow


class RestrictedDownloaderWorkflow(AsyncWorkflow):
    def __init__(self):
        super().__init__()

        self.client = None

    async def get_client(self, account: Account):
        if not self.client:
            self.client = TelegramClient(
                StringSession(
                    account.session_string
                ), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
            )

        await self.client.connect()

        return self.client

    async def prepare(self, process: Process, job: Job):
        """
        Creates jobs to download data from telegram channel
        The next stages: send_ethers_batch, send_ethers, send_tokens
        """
        data = job.data

        from_account_id = data.get('from_account_id')
        if not from_account_id:
            return await self.fail_process(process, job, f'From account id is required.')

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

        channel_id = data.get('channel_id')
        if not channel_id:
            return await self.fail_process(process, job, f'Channel id is required.')

        try:
            channel, text = await fetch_channel_info(client, channel_id)
        except Exception as e:
            await self.process_log(process, str(e))
            return await self.fail_process(process, job, f'Failed to get channel.')

        await self.process_log(process, f'RestrictedDownloaderWorkflow.prepare: {text}')

        chapter_ids = data['chapter_ids', []]
        message_ids = data.get('message_ids', [])

        # fee_job = self.create_job(
        #     stage='send_ethers',
        #     process=process,
        #     parent=job,
        #     data={},
        #     status=JOB_PLANNED,
        # )

        # finish prepare job, this will activate next jobs
        await self.done_job(job)

    async def task1(self, process: Process, job: Job):
        pass
