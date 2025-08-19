#!/usr/bin/env python3
"""
Celery Worker for FinGood Background Tasks

This script runs the Celery worker for processing background jobs including:
- File upload processing
- Bulk categorization
- Export generation
- Analytics calculation

Usage:
    python celery_worker.py [options]

Environment Variables:
    - REDIS_URL: Redis connection URL for message broker
    - DATABASE_URL: Database connection URL
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/celery_worker.log')
    ]
)

logger = logging.getLogger(__name__)

# Import after path setup
from app.core.background_jobs import celery_app
from app.core.config import settings

def main():
    """Main entry point for the Celery worker"""
    try:
        logger.info("Starting FinGood Celery worker...")
        logger.info(f"Redis URL: {settings.REDIS_URL}")
        logger.info(f"Database URL: {settings.DATABASE_URL}")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Start the Celery worker
        celery_app.worker_main([
            'worker',
            '--loglevel=INFO',
            '--concurrency=2',  # Number of worker processes
            '--queues=file_processing,categorization,export,analytics',
            '--hostname=worker@%h',
            '--max-tasks-per-child=1000',
            '--time-limit=1800',  # 30 minutes
            '--soft-time-limit=1500',  # 25 minutes
        ])
        
    except KeyboardInterrupt:
        logger.info("Celery worker stopped by user")
    except Exception as e:
        logger.error(f"Failed to start Celery worker: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
