"""Minimal scheduler: run a research topic repeatedly at a fixed interval.

Usage:
    python -m interface.scheduler --topic "..." --interval 3600
"""
import argparse
import time

from core.logging import get_logger
from core.task_manager import TaskManager

log = get_logger("scheduler")


def run_periodic(topic: str, interval_seconds: int, n_questions: int = 5,
                 max_runs: int = 0) -> None:
    runs = 0
    while True:
        log.info("Scheduled run #%d for topic '%s'", runs + 1, topic)
        tm = TaskManager()
        try:
            tm.run(topic, n_questions=n_questions)
        finally:
            tm.close()
        runs += 1
        if max_runs and runs >= max_runs:
            log.info("Reached max_runs=%d, stopping.", max_runs)
            break
        log.info("Sleeping %d seconds until next run...", interval_seconds)
        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="AutoResearchSystem scheduler")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between runs")
    parser.add_argument("--questions", type=int, default=5)
    parser.add_argument("--max-runs", type=int, default=0, help="0 = run forever")
    args = parser.parse_args()
    run_periodic(args.topic, args.interval, args.questions, args.max_runs)


if __name__ == "__main__":
    main()
