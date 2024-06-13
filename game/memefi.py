import time
from urllib import response
import httpx
import random
import json
from loguru import logger
from datetime import datetime
from tool import JobInfo, format_time, decode_jwt_payload, timestamp_format

headers = {
    "Host": "api-gw-tg.memefi.club",
    "Accept": "*/*",
    "Authorization": "",
    "Sec-Fetch-Site": "same-site",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Sec-Fetch-Mode": "cors",
    "Content-Type": "application/json",
    "Origin": "https://tg-app.memefi.club",
    "User-Agent": "",
    "Referer": "https://tg-app.memefi.club/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
}


class MeMeFi:
    def __init__(self, job_info: JobInfo):
        self.config = job_info
        self.url = "https://api-gw-tg.memefi.club/graphql"
        self.currentHealth = 0
        self.currentEnergy = 0
        self.nonce = ""
        self.token_exp = 0
        self.bot_attempts = 0  # 机器人剩余次数
        self.bot_end_at = 0  # 机器人结束时间
        self.headers = self.make_headers()
        self.client = httpx.Client(verify=False)
        self.num = 0

    def jwt_payload(self) -> bool:
        jwt_info = decode_jwt_payload(self.config.token)
        token_iat = jwt_info.get("iat")
        token_exp = jwt_info.get("exp")
        user_id = jwt_info.get("sub")
        if token_exp < int(time.time()):
            return True
        self.token_exp = token_exp
        logger.info(
            f"MemeFi 登录信息: {user_id}, 登录时间: {timestamp_format(token_iat)}, 过期时间: {timestamp_format(token_exp)}"
        )

    def make_headers(self):
        headers["User-Agent"] = self.config.ua
        headers["Authorization"] = self.config.token
        return headers

    def sync_init(self):
        data = {
            "operationName": "QUERY_GAME_CONFIG",
            "variables": {},
            "query": "query QUERY_GAME_CONFIG {\n  telegramGameGetConfig {\n    ...FragmentBossFightConfig\n    __typename\n  }\n}\n\nfragment FragmentBossFightConfig on TelegramGameConfigOutput {\n  _id\n  coinsAmount\n  currentEnergy\n  maxEnergy\n  weaponLevel\n  energyLimitLevel\n  energyRechargeLevel\n  tapBotLevel\n  currentBoss {\n    _id\n    level\n    currentHealth\n    maxHealth\n    __typename\n  }\n  freeBoosts {\n    _id\n    currentTurboAmount\n    maxTurboAmount\n    turboLastActivatedAt\n    turboAmountLastRechargeDate\n    currentRefillEnergyAmount\n    maxRefillEnergyAmount\n    refillEnergyLastActivatedAt\n    refillEnergyAmountLastRechargeDate\n    __typename\n  }\n  bonusLeaderDamageEndAt\n  bonusLeaderDamageStartAt\n  bonusLeaderDamageMultiplier\n  nonce\n  __typename\n}",
        }
        response = self.client.post(
            self.url,
            data=json.dumps(data, separators=(",", ":")),
            headers=self.headers,
        )
        nonce = response.json().get("data").get("telegramGameGetConfig").get("nonce")
        if nonce != "":
            self.nonce = nonce
            # logger.info(f"MemeFi 初始化 nonce: {self.nonce}")
        else:
            raise Exception("初始化 nonce 失败")

    def send_tap(self):
        data = {
            "operationName": "MutationGameProcessTapsBatch",
            "variables": {
                "payload": {
                    "nonce": "fdf8640efb550372e91e10a86a8070f2110d8c7d0c5c82a866ac2047b40e84bb",
                    "tapsCount": 10,
                }
            },
            "query": "mutation MutationGameProcessTapsBatch($payload: TelegramGameTapsBatchInput!) {\n  telegramGameProcessTapsBatch(payload: $payload) {\n    ...FragmentBossFightConfig\n    __typename\n  }\n}\n\nfragment FragmentBossFightConfig on TelegramGameConfigOutput {\n  _id\n  coinsAmount\n  currentEnergy\n  maxEnergy\n  weaponLevel\n  energyLimitLevel\n  energyRechargeLevel\n  tapBotLevel\n  currentBoss {\n    _id\n    level\n    currentHealth\n    maxHealth\n    __typename\n  }\n  freeBoosts {\n    _id\n    currentTurboAmount\n    maxTurboAmount\n    turboLastActivatedAt\n    turboAmountLastRechargeDate\n    currentRefillEnergyAmount\n    maxRefillEnergyAmount\n    refillEnergyLastActivatedAt\n    refillEnergyAmountLastRechargeDate\n    __typename\n  }\n  bonusLeaderDamageEndAt\n  bonusLeaderDamageStartAt\n  bonusLeaderDamageMultiplier\n  nonce\n  __typename\n}",
        }
        data["variables"]["payload"]["nonce"] = self.nonce
        taps_count = random.randint(*self.config.click_interval)
        data["variables"]["payload"]["tapsCount"] = taps_count
        response = self.client.post(
            self.url,
            data=json.dumps(data, separators=(",", ":")),
            headers=self.headers,
        )
        self.currentHealth = (
            response.json()
            .get("data")
            .get("telegramGameProcessTapsBatch")
            .get("currentBoss")
            .get("currentHealth")
        )  # boss 的当前血量
        self.currentEnergy = (
            response.json()
            .get("data")
            .get("telegramGameProcessTapsBatch")
            .get("currentEnergy")
        )  # 剩余能量
        logger.info(
            "剩余能量: {current_energy}，"
            "Boss 扣除血量: {taps_count}，"
            "Boss 剩余血量: {current_health}，"
            "Boss 击杀预计: {formatted_time}".format(
                current_energy=self.currentEnergy,
                taps_count=taps_count * self.config.click_one,
                current_health=self.currentHealth,
                formatted_time=format_time(
                    int(self.currentHealth / self.config.recovery_seconds)
                ),
            )
        )
        nonce = (
            response.json().get("data").get("telegramGameProcessTapsBatch").get("nonce")
        )
        if nonce == self.nonce:
            logger.error("本次击杀 nonce 未更新，等待 60 秒")
            time.sleep(60)
        else:
            self.nonce = nonce

    def next_boss(self):
        data = {
            "operationName": "telegramGameSetNextBoss",
            "variables": {},
            "query": "mutation telegramGameSetNextBoss {\n  telegramGameSetNextBoss {\n    ...FragmentBossFightConfig\n    __typename\n  }\n}\n\nfragment FragmentBossFightConfig on TelegramGameConfigOutput {\n  _id\n  coinsAmount\n  currentEnergy\n  maxEnergy\n  weaponLevel\n  energyLimitLevel\n  energyRechargeLevel\n  tapBotLevel\n  currentBoss {\n    _id\n    level\n    currentHealth\n    maxHealth\n    __typename\n  }\n  freeBoosts {\n    _id\n    currentTurboAmount\n    maxTurboAmount\n    turboLastActivatedAt\n    turboAmountLastRechargeDate\n    currentRefillEnergyAmount\n    maxRefillEnergyAmount\n    refillEnergyLastActivatedAt\n    refillEnergyAmountLastRechargeDate\n    __typename\n  }\n  bonusLeaderDamageEndAt\n  bonusLeaderDamageStartAt\n  bonusLeaderDamageMultiplier\n  nonce\n  __typename\n}",
        }
        response = self.client.post(
            self.url,
            data=json.dumps(data, separators=(",", ":")),
            headers=self.headers,
        )
        level = (
            response.json()
            .get("data")
            .get("telegramGameSetNextBoss")
            .get("currentBoss")
            .get("level")
        )
        logger.info(f"下一关 Boss 等级: {level}")

    def get_tap_bot_config(self):
        data = {
            "operationName": "TapbotConfig",
            "variables": {},
            "query": "fragment FragmentTapBotConfig on TelegramGameTapbotOutput {\n  damagePerSec\n  endsAt\n  id\n  isPurchased\n  startsAt\n  totalAttempts\n  usedAttempts\n  __typename\n}\n\nquery TapbotConfig {\n  telegramGameTapbotGetConfig {\n    ...FragmentTapBotConfig\n    __typename\n  }\n}",
        }
        for _ in range(3):
            try:
                response = self.client.post(
                    self.url,
                    data=json.dumps(data, separators=(",", ":")),
                    headers=self.headers,
                )
                config = response.json().get("data").get("telegramGameTapbotGetConfig")
                attempts = config.get("totalAttempts") - config.get(
                    "usedAttempts"
                )  # 机器人剩余次数
                self.bot_attempts = attempts
                bot_end_at = config.get("endsAt")  # 任务结束时间
                if bot_end_at is None:  # 机器人暂未开启，或者是刚领取收益
                    logger.info(f"机器人暂未开启，剩余次数: {attempts}")
                    self.bot_end_at = None
                    return
                bot_end_at = datetime.fromisoformat(bot_end_at.replace("Z", "+00:00"))
                logger.info(
                    f"机器人剩余运行次数: {attempts}，机器人结束时间: {bot_end_at}"
                )
                self.bot_end_at = int(bot_end_at.timestamp())
                return
            except Exception as e:
                logger.error(f"获取机器人配置失败: {e}")
                time.sleep(1)
        return False

    # 获取机器人收益
    def tap_bot_claim(self):
        data = {
            "operationName": "TapbotClaim",
            "variables": {},
            "query": "fragment FragmentTapBotConfig on TelegramGameTapbotOutput {\n  damagePerSec\n  endsAt\n  id\n  isPurchased\n  startsAt\n  totalAttempts\n  usedAttempts\n  __typename\n}\n\nmutation TapbotClaim {\n  telegramGameTapbotClaimCoins {\n    ...FragmentTapBotConfig\n    __typename\n  }\n}",
        }
        for _ in range(3):
            try:
                response = self.client.post(
                    self.url,
                    data=json.dumps(data, separators=(",", ":")),
                    headers=self.headers,
                )
                if response.status_code == 200:
                    logger.info("机器人收益领取成功")
                    return
            except Exception as e:
                time.sleep(1)

    # 启动机器人
    def start_tap_bot(self):
        data = {
            "operationName": "TapbotStart",
            "variables": {},
            "query": "fragment FragmentTapBotConfig on TelegramGameTapbotOutput {\n  damagePerSec\n  endsAt\n  id\n  isPurchased\n  startsAt\n  totalAttempts\n  usedAttempts\n  __typename\n}\n\nmutation TapbotStart {\n  telegramGameTapbotStart {\n    ...FragmentTapBotConfig\n    __typename\n  }\n}",
        }
        for _ in range(3):
            try:
                response = self.client.post(
                    self.url,
                    data=json.dumps(data, separators=(",", ":")),
                    headers=self.headers,
                )
                if response.status_code == 200:
                    logger.info("机器人启动成功")
                    return
            except Exception as e:
                time.sleep(1)

    def run(self):
        try:
            if self.token_exp < int(time.time()):
                logger.error("MemeFi 登录信息已过期，请重新登录")
                time.sleep(60 * 60 * 24)
                return
            if self.nonce == "":  # 首次登录
                self.sync_init()
                self.get_tap_bot_config()

            if (self.bot_end_at != None and int(time.time()) > self.bot_end_at) or (
                self.bot_end_at == None and self.bot_attempts > 0
            ):  # 机器人任务结束，或者机器人未开启
                if self.bot_end_at != None:
                    self.tap_bot_claim()  # 领取机器人收益

                self.get_tap_bot_config()  # 获取机器人配置
                if self.bot_end_at == None and self.bot_attempts > 0:
                    self.start_tap_bot()  # 启动机器人

            self.send_tap()
            if self.currentHealth <= 0:
                logger.info("Boss 击杀成功")
                self.next_boss()
                logger.info("Boss 刷新成功，等待 10 分钟后继续")
                time.sleep(600)
            if (
                self.currentEnergy
                <= self.config.click_interval[1] * self.config.click_one
            ):
                count = self.config.capacity - self.currentEnergy  # 需要恢复的能量
                recovery_time = count / self.config.recovery_seconds  # 恢复时间
                sleep_time = random.uniform(recovery_time * 0.93, recovery_time * 0.95)
                logger.info(
                    f"本次能量不足: {self.currentEnergy}, 等待 {sleep_time} 秒后继续"
                )
                time.sleep(sleep_time)
                self.num += 1
                if self.num % 40 == 0:
                    self.get_tap_bot_config()
            else:
                time.sleep(random.uniform(*self.config.sleep_interval))

        except Exception as e:
            logger.exception(e)
            logger.error(f"An unexpected error occurred: {e}")
            time.sleep(60)


def one_meme_fi():
    job_info = JobInfo(
        {
            "ua": "",
            "token": "",
            "capacity": 3000,
            "recovery_seconds": 3,
            "click_one": 4,
            "click_interval": [100, 150],
            "sleep_interval": [1, 5],
        }
    )
    tap_swap = MeMeFi(job_info)
    tap_swap.jwt_payload()
    tap_swap.run()
