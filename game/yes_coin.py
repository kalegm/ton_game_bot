import time
import httpx
from loguru import logger
from random import uniform, randint
from tool import JobInfo, decode_jwt_payload, timestamp_format

headers = {
    "Host": "api.yescoin.gold",
    "Accept": "application/json, text/plain, */*",
    "Sec-Fetch-Site": "same-site",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Token": "",
    "Origin": "https://www.yescoin.gold",
    "User-Agent": "",
    "Referer": "https://www.yescoin.gold/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
}


class YesCoin:
    def __init__(self, job_info: JobInfo) -> None:
        self.config = job_info
        self.offline_url = "https://api.yescoin.gold/user/offline"
        self.get_account_url = "https://api.yescoin.gold/account/getAccountInfo"
        self.collect_coin_url = "https://api.yescoin.gold/game/collectCoin"
        self.client = httpx.Client(verify=False)
        self.headers = self.make_headers()
        self.token_exp = 0

    def jwt_payload(self) -> bool:
        jwt_info = decode_jwt_payload(self.config.token)
        token_iat = jwt_info.get("iat")
        token_exp = jwt_info.get("exp")
        user_id = jwt_info.get("sub")
        if token_exp < int(time.time()):
            return True
        self.token_exp = token_exp
        logger.info(
            f"YesCoin 登录信息: {user_id}, 登录时间: {timestamp_format(token_iat)}, 过期时间: {timestamp_format(token_exp)}"
        )

    def make_headers(self):
        headers["User-Agent"] = self.config.ua
        headers["Token"] = self.config.token
        return headers

    def post_offline(self):
        headers = self.headers.copy()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.client.post(self.offline_url, headers=headers)

    def get_account_info(self):
        headers = self.headers.copy()
        self.client.get(self.get_account_url, headers=headers)

    def get_collectCoin(self):
        random_number = randint(*self.config.click_interval)
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        response = self.client.post(
            url=self.collect_coin_url,
            headers=headers,
            data=str(random_number),
        )
        if response.status_code != 201:
            resp = response.json()
            if resp.get("code") == 0:  # 未登录
                collectAmount = response.json().get("data").get("collectAmount")
                logger.info(f"本次点击: {random_number}, 获取YES金币: {collectAmount}")
            elif resp.get("code") == 400003:
                sleep_time = self.config.capacity / self.config.recovery_seconds
                sleep_time = uniform(sleep_time * 0.94, sleep_time * 0.96)
                logger.info(f"本次点击: 能量不足，等待 {sleep_time} 秒后继续")
                time.sleep(sleep_time)
            else:
                logger.error(f"An unexpected error occurred: {resp}")
        else:
            raise Exception("An unexpected error occurred")

    def run(self) -> int:
        try:
            if self.token_exp < int(time.time()):
                logger.error("YesCoin 登录信息已过期，请重新登录")
                time.sleep(60 * 60 * 24)
                return
            self.post_offline()
            self.get_account_info()
            self.get_collectCoin()
            time.sleep(uniform(*self.config.sleep_interval))
        except Exception as e:
            logger.exception(e)
            logger.error(f"An unexpected error occurred: {e}")
            time.sleep(60)


if __name__ == "__main__":
    yes_coin = YesCoin({})

# https://api.yescoin.gold/build/getAccountBuildInfo 获取可以重置次数 coinPoolLeftRecoveryCount
# https://api.yescoin.gold/game/recoverCoinPool 重置金币池
