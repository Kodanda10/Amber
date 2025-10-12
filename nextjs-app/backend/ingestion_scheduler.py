# backend/ingestion_scheduler.py
"""
Scheduled ingestion service for X (Twitter) posts.
Uses APScheduler for periodic ingestion of posts from pre-listed leaders.
"""
from __future__ import annotations

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pybreaker

logger = logging.getLogger(__name__)

# Configuration from environment variables
X_INGEST_ENABLED = os.getenv("X_INGEST_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
X_BACKFILL_COUNT = int(os.getenv("X_BACKFILL_COUNT", "50"))
X_INGEST_INTERVAL_MINUTES = int(os.getenv("X_INGEST_INTERVAL_MINUTES", "30"))
X_INGEST_CRON = os.getenv("X_INGEST_CRON", "")  # e.g., "*/30 * * * *" for every 30 minutes

# Circuit breaker for X API calls
x_api_circuit_breaker = pybreaker.CircuitBreaker(
    fail_max=5,  # Open circuit after 5 failures
    reset_timeout=300,  # Stay open for 5 minutes (in seconds)
    name="x_api_breaker"
)


class XIngestionScheduler:
    """
    Scheduler for periodic ingestion of X posts from pre-listed leaders.
    
    Features:
    - Configurable scheduling via cron or interval
    - Circuit breaker protection for X API calls
    - Backfill support for initial ingestion
    - Leader list management
    """
    
    def __init__(self, app, db):
        """
        Initialize ingestion scheduler.
        
        Args:
            app: Flask application instance
            db: SQLAlchemy database instance
        """
        self.app = app
        self.db = db
        self.scheduler = BackgroundScheduler(
            daemon=True,
            job_defaults={
                'coalesce': True,  # Combine missed runs
                'max_instances': 1,  # Only one instance of job at a time
                'misfire_grace_time': 300  # 5 minutes grace period
            }
        )
        self.running = False
    
    def start(self):
        """Start the scheduler if X ingestion is enabled."""
        if not X_INGEST_ENABLED:
            logger.info("X ingestion is disabled (X_INGEST_ENABLED=false)")
            return
        
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        # Add ingestion job
        if X_INGEST_CRON:
            # Use cron trigger
            trigger = CronTrigger.from_crontab(X_INGEST_CRON)
            self.scheduler.add_job(
                self._run_ingestion,
                trigger=trigger,
                id='x_ingestion_cron',
                name='X Post Ingestion (Cron)',
                replace_existing=True
            )
            logger.info(f"Scheduled X ingestion with cron: {X_INGEST_CRON}")
        else:
            # Use interval trigger
            trigger = IntervalTrigger(minutes=X_INGEST_INTERVAL_MINUTES)
            self.scheduler.add_job(
                self._run_ingestion,
                trigger=trigger,
                id='x_ingestion_interval',
                name='X Post Ingestion (Interval)',
                replace_existing=True
            )
            logger.info(f"Scheduled X ingestion every {X_INGEST_INTERVAL_MINUTES} minutes")
        
        self.scheduler.start()
        self.running = True
        logger.info("X ingestion scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.scheduler.shutdown(wait=False)
        self.running = False
        logger.info("X ingestion scheduler stopped")
    
    def run_once(self, backfill: bool = False):
        """
        Run ingestion once immediately.
        
        Args:
            backfill: If True, fetch more posts for initial backfill
        """
        with self.app.app_context():
            try:
                self._run_ingestion(backfill=backfill)
            except Exception as e:
                logger.error(f"Error in one-time ingestion: {e}", exc_info=True)
    
    def _run_ingestion(self, backfill: bool = False):
        """
        Run ingestion for all leaders with X handles.
        
        Args:
            backfill: If True, fetch more posts for initial backfill
        """
        with self.app.app_context():
            from app import Leader, ingest_x_posts
            
            # Get all leaders with X handles
            all_leaders = Leader.query.all()
            leaders_with_x = []
            
            for leader in all_leaders:
                if leader.handles and leader.handles.get("x"):
                    leaders_with_x.append(leader)
            
            if not leaders_with_x:
                logger.info("No leaders with X handles found")
                return
            
            logger.info(f"Starting X ingestion for {len(leaders_with_x)} leaders")
            
            success_count = 0
            failure_count = 0
            total_posts = 0
            
            for leader in leaders_with_x:
                try:
                    # Use circuit breaker to protect against X API failures
                    @x_api_circuit_breaker
                    def ingest_leader():
                        return ingest_x_posts(leader.id)
                    
                    posts = ingest_leader()
                    post_count = len(posts) if posts else 0
                    total_posts += post_count
                    success_count += 1
                    
                    logger.info(
                        f"Ingested {post_count} X posts for leader {leader.name} "
                        f"(ID: {leader.id})"
                    )
                    
                except pybreaker.CircuitBreakerError:
                    logger.error(
                        f"Circuit breaker open for X API, skipping leader {leader.name}"
                    )
                    failure_count += 1
                    break  # Stop processing if circuit is open
                    
                except Exception as e:
                    logger.error(
                        f"Failed to ingest X posts for leader {leader.name}: {e}",
                        exc_info=True
                    )
                    failure_count += 1
            
            logger.info(
                f"X ingestion completed: {success_count} succeeded, "
                f"{failure_count} failed, {total_posts} total posts"
            )
    
    def get_status(self) -> Dict:
        """
        Get scheduler status and job information.
        
        Returns:
            Dictionary with scheduler status
        """
        jobs = []
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        
        return {
            "enabled": X_INGEST_ENABLED,
            "running": self.running,
            "circuit_breaker_state": x_api_circuit_breaker.current_state,
            "circuit_breaker_failures": x_api_circuit_breaker.fail_counter,
            "jobs": jobs,
            "config": {
                "backfill_count": X_BACKFILL_COUNT,
                "interval_minutes": X_INGEST_INTERVAL_MINUTES,
                "cron": X_INGEST_CRON or None,
            }
        }


# Global scheduler instance (initialized by app)
_scheduler: Optional[XIngestionScheduler] = None


def get_scheduler() -> Optional[XIngestionScheduler]:
    """Get global scheduler instance."""
    return _scheduler


def init_scheduler(app, db) -> XIngestionScheduler:
    """
    Initialize and start the global scheduler.
    
    Args:
        app: Flask application instance
        db: SQLAlchemy database instance
    
    Returns:
        Initialized scheduler instance
    """
    global _scheduler
    _scheduler = XIngestionScheduler(app, db)
    _scheduler.start()
    return _scheduler
