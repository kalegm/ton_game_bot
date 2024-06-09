import json
import random
import time
import arrow
import httpx
from tool import JobInfo, decode_jwt_payload, timestamp_format
from loguru import logger

headers = {
    "Host": "api.tapswap.ai",
    "x-cv": "621",
    "Accept": "*/*",
    "Authorization": "",
    "Content-Id": "",
    "Sec-Fetch-Site": "cross-site",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Origin": "https://app.tapswap.club",
    "User-Agent": "",
    "Referer": "https://app.tapswap.club/",
    "x-bot": "no",
    "x-app": "tapswap_server",
    "Sec-Fetch-Dest": "empty",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
}


def hs(dollar, W):
    result = float(dollar) * float(W)
    return int(result) % dollar


class TapSwap:
    def __init__(self, job_info: JobInfo) -> None:
        self.config = job_info
        self.submit_taps_url = "https://api.tapswap.ai/api/player/submit_taps"
        self.client = httpx.Client(verify=False)
        self.energy = 0
        self.token_exp = 0
        self.uid = 0

    def make_headers(self):
        headers["User-Agent"] = self.config.ua
        headers["Authorization"] = self.config.token
        return headers

    def jwt_payload(self) -> bool:
        jwt_info = decode_jwt_payload(self.config.token)
        token_iat = jwt_info.get("iat")
        token_exp = jwt_info.get("exp")
        user_id = jwt_info.get("sub")
        if token_exp < int(time.time()):
            return True
        self.token_exp = token_exp
        self.uid = user_id
        logger.info(
            f"Tap_Swap 登录信息: {user_id}, 登录时间: {timestamp_format(token_iat)}, 过期时间: {timestamp_format(token_exp)}"
        )

    def submit_taps(self) -> None:
        taps = random.randint(*self.config.click_interval)
        current_mill_time = int(arrow.utcnow().timestamp() * 1000)
        client_id = hs(self.uid, current_mill_time)
        headers = self.make_headers().copy()
        headers["Content-Id"] = str(client_id)
        response = self.client.post(
            url=self.submit_taps_url,
            headers=headers,
            data=json.dumps(
                {"taps": taps, "time": current_mill_time}, separators=(",", ":")
            ),
        )
        resp = response.json()
        if resp.get("statusCode") == 400:
            raise Exception("invalid_request[2]")

        energy = resp.get("player").get("energy")
        logger.info(
            f"本次增加 {taps * self.config.click_one} Tap 金币, 剩余能量 {energy}"
        )
        self.energy = energy

    def run(self):
        try:
            if self.token_exp == 0:
                self.jwt_payload()
            if self.token_exp < int(time.time()):
                logger.error("Tap Swap 登录信息已过期，请重新登录")
                time.sleep(60 * 60 * 24)
                return

            self.submit_taps()

            if self.energy <= self.config.click_interval[1] * self.config.click_one:
                count = self.config.capacity - self.energy
                recovery_time = count / self.config.recovery_seconds
                sleep_time = random.uniform(recovery_time * 0.93, recovery_time * 0.95)
                logger.info(f"本次点击：能量剩余不足，等待 {sleep_time} 秒后继续")
                time.sleep(sleep_time)
            else:
                time.sleep(random.uniform(*self.config.sleep_interval))

        except Exception as e:
            logger.exception(f"TapSwap 出错: {e}")
            time.sleep(60)


def one_tap_swap():
    job_info = JobInfo(
        {
            "ua": "",
            "token": "",
            "capacity": 2500,
            "recovery_seconds": 3,
            "click_one": 4,
            "click_interval": [1300, 1500],
            "sleep_interval": [1, 5],
        }
    )
    tap_swap = TapSwap(job_info)  # 开启 Taping Guru 直接提交 1200~1400 次
    tap_swap.run()
