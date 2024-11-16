from aiogram.fsm.state import State, StatesGroup


class RestrictedDownloaderForm(StatesGroup):
    restricted_downloader_session = State()

    get_phone_number = State()
    get_code = State()
    get_password = State()

    select_dialog = State()
    select_sender_account = State()
    select_receiver_account = State()
