import httpx
import arrow
import json
import time
from loguru import logger
from random import uniform, randint
from tool import JobInfo

headers = {
    "Host": "api.hamsterkombat.io",
    "Accept": "application/json",
    "Authorization": "",
    "Sec-Fetch-Site": "same-site",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Origin": "https://hamsterkombat.io",
    "User-Agent": "",
    "Referer": "https://hamsterkombat.io/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Content-Type": "application/json",
}


class Hamster:

    def __init__(self, job_info: JobInfo):
        self.config = job_info
        self.sync_url = "https://api.hamsterkombat.io/clicker/sync"
        self.click_url = "https://api.hamsterkombat.io/clicker/tap"
        self.available_taps = 0
        self.last_sync_update = 0
        self.boost_earn_per_tap = 0
        self.headers = self.update_headers()
        self.client = httpx.Client(verify=False)

    def update_headers(self):
        headers["User-Agent"] = self.config.ua
        headers["Authorization"] = self.config.token
        return headers

    def sync_init(self):
        response = self.client.post(
            url=self.sync_url,
            headers=self.headers,
        )
        if response.status_code != 200:
            raise Exception(f"Error sending POST request: {response.status_code}")
        availableTaps = response.json().get("clickerUser").get("availableTaps")
        lastSyncUpdate = response.json().get("clickerUser").get("lastSyncUpdate")
        if availableTaps and lastSyncUpdate:
            self.available_taps = availableTaps
            self.last_sync_update = lastSyncUpdate
            logger.info(
                f"仓鼠初始化金币: {self.available_taps}, 上次同步时间: {self.last_sync_update}"
            )
            return
        raise Exception("Failed to initialize")

    def click_tap(self):
        count = randint(*self.config.click_interval)
        now_time = int(arrow.now().timestamp())
        self.available_taps += (
            now_time - self.last_sync_update
        ) * self.config.recovery_seconds
        self.available_taps -= self.config.click_one * count
        if self.available_taps < 0:
            return
        response = self.client.post(
            url=self.click_url,
            headers=self.headers,
            data=json.dumps(
                {
                    "count": count,
                    "availableTaps": self.available_taps,
                    "timestamp": now_time,
                },
                separators=(",", ":"),
            ),
        )
        if response.status_code == 200:
            available_taps = response.json().get("clickerUser").get("availableTaps")
            last_sync_update = response.json().get("clickerUser").get("lastSyncUpdate")
            if available_taps and last_sync_update:
                self.available_taps = available_taps
                self.last_sync_update = last_sync_update
                logger.info(
                    f"仓鼠剩余金币: {self.available_taps}, 本次扣除: {count * self.config.click_one}"
                )
                return
        raise Exception(f"Error sending POST request: {response.status_code}")

    def run(self):
        try:
            if self.available_taps == 0 or self.last_sync_update == 0:
                self.sync_init()

            if (
                self.available_taps
                <= self.config.click_interval[1] * self.config.click_one
            ):  # 低于最低点击数
                count = self.config.capacity - self.available_taps  # 需要恢复的金币
                recovery_time = count / self.config.recovery_seconds
                sleep_time = uniform(recovery_time * 0.93, recovery_time * 0.95)
                logger.info(f"本次点击: 仓鼠剩余金币不足，等待 {sleep_time} 秒后继续")
                time.sleep(sleep_time)
                self.available_taps = 0
                self.last_sync_update = 0
                return

            self.click_tap()
            time.sleep(uniform(*self.config.sleep_interval))
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            time.sleep(60)


# 判断是否可以开启 full energy 冷却时间一小时
