import random
import time
import httpx
from tool import JobInfo
from loguru import logger

headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Accept": "*/*",
    "Authorization": "",
    "Sec-Fetch-Site": "cross-site",
    "Access-Control-Allow-Headers": "*",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Mode": "cors",
    "Host": "cat-backend.pro",
    "Origin": "https://tg-purr-tap.vercel.app",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Referer": "https://tg-purr-tap.vercel.app/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
}


class TapCat:
    def __init__(self, job_info: JobInfo) -> None:
        self.config = job_info
        self.client = httpx.Client(verify=False)
        self.mining_url = "https://cat-backend.pro/v1/points/mining"
        self.profile_url = "https://cat-backend.pro/v1/auth/profile"
        self.headers = self.update_headers()

    def update_headers(self):
        headers["Authorization"] = self.config.token
        return headers

    def start_mining(self):
        for _ in range(3):
            try:
                response = self.client.get(
                    url=self.mining_url,
                    headers=self.headers,
                )
                if response.status_code == 200:
                    points_per_second = response.json().get("points_per_second")
                    if points_per_second != None:
                        logger.info(f"初始化 mined {points_per_second}")
                        return
            except Exception as e:
                time.sleep(1)

    def end_mining(self):
        for _ in range(3):
            try:
                response = self.client.post(
                    url=self.mining_url,
                    headers=self.headers,
                )
                if response.status_code == 200:
                    total_mined_points = response.json().get("total_mined_points")
                    if total_mined_points != None:
                        logger.info(f"获取 mined {total_mined_points}")
                        return
            except Exception as e:
                time.sleep(1)

    def get_profile(self):
        response = self.client.get(
            url=self.profile_url,
            headers=self.headers,
        )
        if response.status_code == 200:
            total_points = response.json().get("total_points")
            logger.info(f"当前额度 {total_points}")
        else:
            logger.info("获取额度失败")

    def run(self):
        try:
            self.start_mining()
            sleep_time = random.randint(*self.config.sleep_interval)
            logger.info(f"mining 开始，等待 {sleep_time} 秒")
            time.sleep(sleep_time)
            self.end_mining()
            self.get_profile()
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            time.sleep(10 * 60)
