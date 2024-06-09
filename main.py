import sys
import threading
from loguru import logger
from game import YesCoin, Hamster, MeMeFi, TapSwap, one_tap_swap
from tool import load_config, JobInfo

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | <red>{level: <5}</red> | <green>{file: <12}</green> | {message}",
)

job_func_map = {
    "hamster": Hamster,
    "yes_coin": YesCoin,
    "memefi": MeMeFi,
    "tap_swap": TapSwap,
}


class Scheduler:
    def __init__(self, config: dict):
        self.config = config

    def run_job(self, job_id: str, job_config: dict):
        if job_id not in job_func_map:
            return

        job_info = JobInfo(job_config)

        func = job_func_map[job_id](job_info=job_info)
        if isinstance(func, type):
            func = func()

        if hasattr(func, "jwt_payload"):
            if func.jwt_payload():
                logger.error(f"当前任务 {job_id} 登录信息已过期，请重新登录")
                return

        while True:
            func.run()

    def run(self):
        logger.info("Start running tasks")
        threads = []
        game_config = self.config.get("game", {})
        client_config = self.config.get("client", {})

        for job_id, job_config in game_config.items():
            if job_config["enabled"]:
                logger.info(f"Running job: {job_id}")
                job_config.update(client_config)
                thread = threading.Thread(
                    target=self.run_job, args=(job_id, job_config)
                )
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()


def main():

    config = load_config("config.toml")
    scheduler = Scheduler(config)
    try:
        scheduler.run()
    except KeyboardInterrupt:
        print("Task terminated by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
