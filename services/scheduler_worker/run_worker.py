"""Run RQ worker for default queue."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from redis import Redis
from rq import Worker, Queue

from libs.common.config import get_settings

def main():
    redis = Redis.from_url(get_settings().redis_url)
    queues = [Queue("default", connection=redis)]
    worker = Worker(queues, connection=redis)
    worker.work()

if __name__ == "__main__":
    main()
