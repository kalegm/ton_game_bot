import random
import json
import time
import httpx
from tool import JobInfo
from loguru import logger
from tool import JobInfo, decode_jwt_payload, timestamp_format

headers = {
    "Accept": "application/json, text/plain, */*",
    "Authorization": "",
    "Sec-Fetch-Site": "same-site",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Host": "game-domain.blum.codes",
    "Origin": "https://telegram.blum.codes",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Sec-Fetch-Dest": "empty",
}


class Blum:
    def __init__(self, job_info: JobInfo) -> None:
        self.config = job_info
        self.client = httpx.Client(verify=False)
        self.play_url = "https://game-domain.blum.codes/api/v1/game/play"
        self.claim_url = "https://game-domain.blum.codes/api/v1/game/claim"
        self.balance_url = "https://game-domain.blum.codes/api/v1/user/balance"
        self.headers = self.update_headers()
        self.play_passes = 0
        self.token_exp = 0

    def update_headers(self):
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
        logger.info(
            f"Blum 登录信息: {user_id}, 登录时间: {timestamp_format(token_iat)}, 过期时间: {timestamp_format(token_exp)}"
        )

    def game_play(self):
        for _ in range(3):
            try:
                resp = self.client.post(url=self.play_url, headers=self.headers)
                if resp.status_code == 200:
                    game_id = resp.json().get("gameId")
                    logger.info(f"游戏开始 {game_id}")
                    return game_id
                time.sleep(2)
            except Exception as e:
                time.sleep(2)

    def game_claim(self, game_id):
        for _ in range(3):
            try:
                headers = self.headers.copy()
                headers["Content-Type"] = "application/json"
                points = random.randint(211, 235)
                resp = self.client.post(
                    url=self.claim_url,
                    headers=headers,
                    data=json.dumps(
                        {
                            "gameId": game_id,
                            "points": points,
                        },
                        separators=(",", ":"),
                    ),
                )
                if resp.status_code == 200:
                    logger.info(f"游戏结束{resp.text}, 获得 {points} 个")
                    return
                logger.error(f"游戏异常 {resp.text}")
                time.sleep(4)
            except Exception as e:
                logger.error(f"游戏出现异常{e}")
                time.sleep(4)

    def user_info(self):
        for _ in range(3):
            try:
                resp = self.client.get(url=self.balance_url, headers=self.headers)
                if resp.status_code == 200:
                    self.play_passes = resp.json().get("playPasses")
                    balance = resp.json().get("availableBalance")
                    logger.info(
                        f"当前游戏剩余次数 {self.play_passes}, 当前代币 {balance}"
                    )
                    return
                time.sleep(2)
            except Exception as e:
                time.sleep(2)

    def run(self):
        try:
            if self.token_exp == 0:
                self.jwt_payload()

            if self.token_exp < int(time.time()):
                logger.error("Blum 登录信息已过期，请重新登录")
                time.sleep(60 * 60 * 24)
                return

            self.user_info()
            if self.play_passes < 1:
                logger.error("游戏次数不足")
                time.sleep(60 * 60 * 24)
                return

            game_id = self.game_play()
            sleep_time = random.uniform(*self.config.sleep_interval)
            logger.info(f"本次游戏游玩时间 {sleep_time}")

            if game_id != None:
                time.sleep(sleep_time)
                self.game_claim(game_id=game_id)
                time.sleep(random.uniform(2, 5))  # 等待两秒开始游戏
            else:
                logger.error("游戏开始失败")
                time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"blum 错误 {e}")
            time.sleep(30)
