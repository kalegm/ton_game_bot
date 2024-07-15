import random
import time
import httpx
from tool import JobInfo
from loguru import logger

headers = {
    "Host": "api-clicker.pixelverse.xyz",
    "Accept": "application/json, text/plain, */*",
    "Tg-Id": "",
    "Sec-Fetch-Site": "cross-site",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Secret": "",
    "Origin": "https://sexyzbot.pxlvrs.io",
    "Initdata": "",
    "Username": "kagalaw",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": "https://sexyzbot.pxlvrs.io/",
    "Sec-Fetch-Dest": "empty",
    "Connection": "keep-alive",
}


class PixelTap:
    def __init__(self, job_info: JobInfo) -> None:
        self.config = job_info
        self.client = httpx.Client(verify=False)
        self.url = "https://api-clicker.pixelverse.xyz/api/mining/claim"

    def mining_claim(self):
        headers["Secret"] = self.config.get("secret")
        headers["Tg-Id"] = self.config.get("tg_id")
        headers["Initdata"] = self.config.get("init_data")
        for _ in range(3):
            response = self.client.post(self.url, headers=headers)
            if response.status_code == 201:
                resp = response.json()
                claimedAmount = resp.get("claimedAmount", 0)
                logger.info(f"mining claim: {claimedAmount}")
                break

    def run(self):
        try:
            self.mining_claim()
            sleep_time = random.randint(*self.config.sleep_interval)
            logger.info(f"本次点击结束，休息 {sleep_time} 秒")
            time.sleep(sleep_time)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            time.sleep(60 * 60)
