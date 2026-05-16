import logging
import uuid

logger = logging.getLogger(__name__)


def enqueue_review_run(developer_run_id: uuid.UUID) -> None:
    """Dispatch the auto-review Celery task for a completed developer run."""
    try:
        from src.services.review_runner import dispatch_review_run  # noqa: PLC0415

        dispatch_review_run.delay(str(developer_run_id))
        logger.info("Enqueued dispatch_review_run for developer run %s.", developer_run_id)
    except ImportError:
        logger.warning("[REVIEW] dispatch_review_run not importable — skipping auto-review.")
    except Exception as exc:
        logger.warning("[REVIEW] Failed to enqueue review for run %s: %s.", developer_run_id, exc)
