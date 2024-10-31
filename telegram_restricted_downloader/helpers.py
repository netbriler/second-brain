import ipaddress
import struct
import time

from telethon import TelegramClient
from telethon.sessions import StringSession

_STRUCT_PREFORMAT = '>B{}sH256s'

CURRENT_VERSION = '1'


def humanbytes(size: int) -> str:
    if size == 0:
        return '0 B'
    power = 2 ** 10
    n = 0
    dic_power_n = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size >= power and n < 4:
        size /= power
        n += 1
    return f'{round(size, 2)} {dic_power_n[n]}B'


class DownloadStats:
    def __init__(self, current: int, speed: float, time_left: float, downloaded: int, total: int):
        self.current = current
        self.speed = speed
        self.time_left = time_left
        self.downloaded = downloaded
        self.total = total

    @property
    def progress_percentage(self) -> float:
        return (self.current / self.total) * 100 if self.total > 0 else 0

    def format_time(self, seconds: float) -> str:
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        tmp = ''
        if days > 0:
            tmp += f'{days}d, '
        if hours > 0:
            tmp += f'{hours}h, '
        if minutes > 0:
            tmp += f'{minutes}m, '
        if seconds > 0:
            tmp += f'{seconds}s'
        return tmp.strip(', ')

    def __repr__(self):
        return (
            f'DownloadStats(progress={self.progress_percentage:.2f}%, '
            f'speed={humanbytes(int(self.speed))}/s, '
            f'downloaded={humanbytes(self.downloaded)} / {humanbytes(self.total)}, '
            f'time_left={self.format_time(self.time_left)})'
        )


class ProgressTracker:
    def __init__(self, total: int = 0):
        self.total = total
        self.start_time = time.time()
        self.last_time = self.start_time
        self.last_bytes = 0
        self.speed = 0
        self.current = 0
        self.time_left = float('inf')
        self.stats = DownloadStats(
            current=self.current,
            speed=self.speed,
            time_left=self.time_left,
            downloaded=0,
            total=0,
        )

    def callback(self, current: int, total: int) -> DownloadStats:
        self.current = current
        self.total = total
        current_time = time.time()
        delta_time = current_time - self.last_time
        delta_bytes = current - self.last_bytes

        # Update last tracked time and bytes
        self.last_time = current_time
        self.last_bytes = current

        # Calculate download speed (bytes per second)
        self.speed = delta_bytes / delta_time if delta_time > 0 else 0

        # Calculate estimated time left
        bytes_left = self.total - current
        self.time_left = bytes_left / self.speed if self.speed > 0 else float('inf')

        # Create the stats object
        self.stats = DownloadStats(
            current=self.current,
            speed=self.speed,
            time_left=self.time_left,
            downloaded=self.current,
            total=self.total,
        )

        return self.stats


class CustomTelethonClient(TelegramClient):
    def get_session_string(self):
        ip = ipaddress.ip_address(self.session.server_address).packed
        return CURRENT_VERSION + StringSession.encode(
            struct.pack(
                _STRUCT_PREFORMAT.format(len(ip)), self.session.dc_id, ip, self.session.port,
                self.session.auth_key.key
            )
        )
