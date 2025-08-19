#!/usr/bin/env python3
"""
Flower Monitoring for FinGood Celery Tasks

This script runs Flower, a web-based tool for monitoring and administrating Celery clusters.

Usage:
    python flower_monitor.py

Environment Variables:
    - REDIS_URL: Redis connection URL for message broker
    - FLOWER_PORT: Port for Flower web interface (default: 5555)
    - FLOWER_HOST: Host for Flower web interface (default: 0.0.0.0)
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import after path setup
from app.core.background_jobs import celery_app
from app.core.config import settings

def main():
    """Main entry point for Flower monitoring"""
    try:
        logger.info("Starting FinGood Flower monitoring...")
        logger.info(f"Redis URL: {settings.REDIS_URL}")
        
        # Get Flower configuration from environment
        flower_port = int(os.getenv('FLOWER_PORT', 5555))
        flower_host = os.getenv('FLOWER_HOST', '0.0.0.0')
        
        logger.info(f"Flower will be available at http://{flower_host}:{flower_port}")
        
        # Import and run Flower
        from flower import conf
        from flower.app import Flower
        
        # Configure Flower
        conf.broker_api = settings.REDIS_URL
        conf.port = flower_port
        conf.address = flower_host
        conf.basic_auth = None  # Disable basic auth for development
        conf.enable_events = True
        conf.persistent = True
        conf.db = 'flower.db'
        conf.max_tasks = 10000
        
        # Start Flower
        flower = Flower(celery_app=celery_app)
        flower.start()
        
    except KeyboardInterrupt:
        logger.info("Flower monitoring stopped by user")
    except Exception as e:
        logger.error(f"Failed to start Flower monitoring: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
