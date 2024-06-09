import arrow
import toml
import os
import base64, json


def load_config(config_file):
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file '{config_file}' does not exist.")

    with open(config_file, "r") as file:
        return toml.load(file)


def decode_jwt_payload(token):
    if token.startswith("Bearer "):
        token = token[7:]
    token = token[7:]
    token_body = token.split(".")[1]
    missing_padding = len(token_body) % 4
    if missing_padding != 0:
        token_body += "=" * (4 - missing_padding)
    return json.loads(base64.b64decode(token_body + "=").decode("utf-8"))


def format_time(seconds) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}小时{minutes}分钟{seconds}秒"


def timestamp_format(timestamp) -> str:
    time = arrow.Arrow.fromtimestamp(timestamp)
    formatted_time = time.format("YYYY-MM-DD HH:mm:ss")
    return formatted_time


class JobInfo:
    def __init__(self, job_info) -> None:
        self._data = job_info

    @property
    def enabled(self):
        return self._data.get("enabled", False)

    @property
    def ua(self):
        return self._data.get("ua")

    @property
    def token(self):
        return self._data.get("token")

    @property
    def click_interval(self):
        return self._data.get("click_interval")

    @property
    def sleep_interval(self):
        return self._data.get("sleep_interval")

    @property
    def click_one(self):
        return self._data.get("click_one")

    @property
    def capacity(self):
        return self._data.get("capacity")

    @property
    def recovery_seconds(self):
        return self._data.get("recovery_seconds")
