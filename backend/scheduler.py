"""데이터 수집 스케줄러"""

import logging
import atexit
from typing import Optional

logger = logging.getLogger(__name__)

# APScheduler는 선택적 의존성
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logger.warning("APScheduler가 설치되지 않았습니다. 스케줄링 기능이 비활성화됩니다.")

_scheduler: Optional["BackgroundScheduler"] = None


def get_scheduler() -> Optional["BackgroundScheduler"]:
    """스케줄러 인스턴스 반환"""
    global _scheduler
    return _scheduler


def setup_scheduler(
    collection_hours: str = "6,18",
    collection_interval_hours: Optional[int] = None,
) -> Optional["BackgroundScheduler"]:
    """스케줄러 설정 및 시작

    Args:
        collection_hours: 수집 실행 시간 (cron 형식, 기본값: 오전 6시, 오후 6시)
        collection_interval_hours: 주기적 수집 간격 (시간). 설정 시 cron 대신 사용.

    Returns:
        BackgroundScheduler 인스턴스 또는 None (APScheduler 미설치 시)
    """
    global _scheduler

    if not SCHEDULER_AVAILABLE:
        logger.warning("APScheduler 미설치로 스케줄러를 시작할 수 없습니다.")
        return None

    if _scheduler is not None:
        logger.warning("스케줄러가 이미 실행 중입니다.")
        return _scheduler

    _scheduler = BackgroundScheduler(
        timezone="Asia/Seoul",
        job_defaults={"coalesce": True, "max_instances": 1},
    )

    # 수집 작업 등록
    from collect_data import run_collection

    if collection_interval_hours:
        # 주기적 실행
        _scheduler.add_job(
            run_collection,
            trigger=IntervalTrigger(hours=collection_interval_hours),
            id="periodic_collection",
            name="주기적 데이터 수집",
            replace_existing=True,
        )
        logger.info(f"스케줄러: {collection_interval_hours}시간 간격 수집 등록")
    else:
        # Cron 실행
        _scheduler.add_job(
            run_collection,
            trigger=CronTrigger(hour=collection_hours),
            id="daily_collection",
            name="정기 데이터 수집",
            replace_existing=True,
        )
        logger.info(f"스케줄러: 매일 {collection_hours}시 수집 등록")

    _scheduler.start()
    logger.info("스케줄러 시작됨")

    # 프로세스 종료 시 스케줄러 정리
    atexit.register(shutdown_scheduler)

    return _scheduler


def shutdown_scheduler() -> None:
    """스케줄러 종료"""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("스케줄러 종료됨")


def trigger_collection_now() -> bool:
    """즉시 수집 실행 (스케줄러 외부에서 호출)

    Returns:
        True: 작업 트리거 성공, False: 실패
    """
    if _scheduler is None:
        logger.warning("스케줄러가 실행 중이 아닙니다.")
        return False

    try:
        job = _scheduler.get_job("daily_collection") or _scheduler.get_job(
            "periodic_collection"
        )
        if job:
            job.modify(next_run_time=None)  # 즉시 실행
            _scheduler.wakeup()
            logger.info("수집 작업 즉시 실행 트리거됨")
            return True
    except Exception as e:
        logger.error(f"수집 트리거 실패: {e}")

    return False


def get_scheduler_status() -> dict:
    """스케줄러 상태 조회"""
    if _scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
        )

    return {"running": _scheduler.running, "jobs": jobs}
