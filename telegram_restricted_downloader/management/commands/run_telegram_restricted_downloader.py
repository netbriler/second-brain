from datetime import datetime
from getpass import getpass

from django.conf import settings
from django.core.management.base import BaseCommand
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.network import ConnectionTcpAbridged
from telethon.sessions import StringSession
from telethon.tl.types import MessageActionTopicCreate, Dialog

from telegram_restricted_downloader.models import Account

_STRUCT_PREFORMAT = '>B{}sH256s'

CURRENT_VERSION = '1'


class InteractiveTelegramClient(TelegramClient):
    def __init__(
            self, session_user_id, api_id, api_hash,
            proxy=None
    ):
        print('Initializing interactive example...')
        super().__init__(
            session_user_id, api_id, api_hash,
            connection=ConnectionTcpAbridged,
            proxy=proxy
        )

        self.found_media = {}

    async def init(self):
        print('Connecting to Telegram servers...')
        try:
            await self.connect()
        except IOError:
            print('Initial connection failed. Retrying...')
            await self.connect()

        if not await self.is_user_authorized():
            print('First run. Sending code request...')
            user_phone = input('Enter your phone: ')
            await self.sign_in(user_phone)

            self_user = None
            while self_user is None:
                code = input('Enter the code you just received: ')
                try:
                    self_user = await self.sign_in(code=code)

                except SessionPasswordNeededError:
                    pw = getpass(
                        'Two step verification is enabled. '
                        'Please enter your password: '
                    )

                    self_user = await self.sign_in(password=pw)


client = TelegramClient(
    StringSession(

        "1BJWap1sBu3n2hwX1afKMYPhU8VnMlHRersXB2QlHkarWe2QnhARMviLJZ2s8uMGEHK_BhdxkhXlob-lgfXyd_1izJys9wKjEpV7XzPpQ932WXudadYJPN1RZE4cqSsDpwii_XLXy8UZhzchre0HkuE1QGA81lCI5hUCPLrh28cTW3J8VCgorDVvx_qRJMzVtB_-GX6vWfZzt6NAlrhd8Ze3SX401vIdybO8Bv4qIcoEhaHLBtW472_SIh145mkSeiYXfHHNvnhWB3S2dhjrNadHLM89H1MF3crN7ZMqrNcYFi7alUtPbCMQd4pR3AXuLlvf8vEYT1kp2ctIe0uZFZ9QD7gzIHbI="
    ), settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH
)


def datetime_handler(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


print(Dialog)

async def main():
    await client.connect()
    # print(await client.get_me())

    # https: // t.me / c / 2025969435 / 165 / 183

    channel = await client.get_entity(-1002025969435)

    messages = await client.get_messages(channel, ids=[165, 183])
    for message in messages:
        print(isinstance(message.action, MessageActionTopicCreate), message.action)

    async for message in client.iter_messages(channel, reply_to=165, limit=1):
        print(message)


    # async for message in client.iter_messages(channel, search='шаг'):
    #     print(message)

    # async for acount in Account.objects.all():
    #     print(acount.name)
    #     print(acount.session_string)
    #     print(acount.encrypted_session_string)

    # return
    # path = str(settings.BASE_DIR / 'temp/test2')
    # print(path)
    #
    # client = InteractiveTelegramClient(path, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    # await client.connect()
    #
    # if not await client.is_user_authorized():
    #     phone = '923163503747'
    #     phone_code_hash = '01f61cadbb78559c33'
    #     # await client.sign_in(phone)
    #     # phone, phone_code_hash = client._parse_phone_and_hash(None, None)
    #     # print(phone, phone_code_hash)
    #     # #
    #     # client = InteractiveTelegramClient(path, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    #     # await client.connect()
    #     code = input('Enter the code you just received: ')
    #     print(code)
    #     try:
    #         self_user = await client.sign_in(
    #             code=code,
    #             phone=phone, phone_code_hash=phone_code_hash
    #         )
    #     except SessionPasswordNeededError:
    #         client = InteractiveTelegramClient(path, settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH)
    #         await client.connect()
    #
    #         pw = getpass(
    #             'Two step verification is enabled. '
    #             'Please enter your password: '
    #         )
    #
    #         self_user = await client.sign_in(password=pw)
    # else:
    #     self_user = await client.get_me()
    #
    # print(f'{self_user.id} {self_user.first_name} {self_user.last_name} ({self_user.username})')
    #
    # ip = ipaddress.ip_address(client.session.server_address).packed
    # session_string = CURRENT_VERSION + StringSession.encode(
    #     struct.pack(
    #         _STRUCT_PREFORMAT.format(len(ip)),
    #         client.session.dc_id,
    #         ip,
    #         client.session.port,
    #         client.session.auth_key.key
    #     )
    # )
    # print(session_string)
    #
    # # detete path file
    # if Path(path + '.session').exists():
    #     Path(path + '.session').unlink()
    #
    # return
    # await client.start()
    #
    # async for m in client.iter_dialogs(archived=False):
    #     print(m)
    #
    # return
    #
    # channel = await client.get_entity(-1001629147115)
    #
    # messages = await client.get_messages(channel, ids=[5834])
    # message = messages[0]
    #
    # await client.download_media(message, './downloads/', progress_callback=ProgressTracker().callback)
    #
    # # print(await client.get_me())
    #
    # # print(await client.upload_file('test.jpg'))
    #
    # # async for mes in client.iter_messages(await client.get_input_entity(-1002150591486), limit=10):
    # #     print(mes)
    #


class Command(BaseCommand):
    help = 'Start telegram bot polling'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        client.loop.run_until_complete(main())
