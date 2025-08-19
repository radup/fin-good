#!/usr/bin/env python3
"""
Simple RQ Worker for FinGood Background Jobs

This is a simplified worker script for quick development and testing.
For production use, prefer start_worker.py which includes comprehensive
monitoring, health checks, and process management.

Usage:
    python worker.py                    # Start worker for all queues
    python worker.py critical high      # Start worker for specific queues

Environment Variables:
    REDIS_URL: Redis connection URL (required)
"""

import sys
import logging
from typing import List

# Add the app directory to Python path
sys.path.insert(0, 'app')

from app.core.background_jobs import start_worker
from app.core.logging_config import setup_logging

def main():
    """Simple worker startup"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get queue names from command line args
    if len(sys.argv) > 1:
        queue_names = sys.argv[1:]
    else:
        queue_names = ['critical', 'high', 'default', 'low']
    
    logger.info(f"Starting simple RQ worker for queues: {queue_names}")
    
    try:
        start_worker(queue_names)
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()