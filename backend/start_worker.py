#!/usr/bin/env python3
"""
RQ Worker Startup Script for FinGood Financial Platform

This script starts RQ workers for processing background jobs in the FinGood platform.
It supports different deployment scenarios and provides comprehensive monitoring,
logging, and graceful shutdown capabilities.

Usage:
    python start_worker.py                          # Start worker for all queues
    python start_worker.py --queues critical,high  # Start worker for specific queues
    python start_worker.py --workers 4             # Start multiple workers
    python start_worker.py --daemon               # Run as daemon process
    
Production Usage:
    # Start dedicated workers for different priorities
    python start_worker.py --queues critical --workers 2
    python start_worker.py --queues high --workers 3  
    python start_worker.py --queues default --workers 5
    python start_worker.py --queues low --workers 2
    
Environment Variables:
    REDIS_URL: Redis connection URL (required)
    LOG_LEVEL: Logging level (default: INFO)
    WORKER_TIMEOUT: Job timeout in seconds (default: 1800)
    WORKER_TTL: Worker time-to-live in seconds (default: 3600)
"""

import argparse
import logging
import os
import signal
import sys
import time
from typing import List, Optional
import multiprocessing as mp
from datetime import datetime

import redis
from rq import Worker, Queue, Connection
from rq.exceptions import WorkerException

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.core.logging_config import setup_logging

# Setup logging
logger = logging.getLogger(__name__)

class FinGoodWorker:
    """
    Enhanced RQ Worker for FinGood with production-ready features.
    
    Features:
    - Graceful shutdown handling
    - Health monitoring and metrics
    - Comprehensive error handling
    - Performance monitoring
    - Resource management
    """
    
    def __init__(
        self,
        queue_names: List[str],
        worker_id: Optional[str] = None,
        timeout: int = 1800,
        ttl: int = 3600
    ):
        self.queue_names = queue_names
        self.worker_id = worker_id or f"worker-{os.getpid()}"
        self.timeout = timeout
        self.ttl = ttl
        self.shutdown_requested = False
        self.start_time = datetime.utcnow()
        
        # Initialize Redis connection
        try:
            self.redis_conn = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=30,
                socket_connect_timeout=30,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            self.redis_conn.ping()
            logger.info(f"Worker {self.worker_id} connected to Redis successfully")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        # Initialize queues
        self.queues = [Queue(name, connection=self.redis_conn) for name in queue_names]
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info(f"Worker {self.worker_id} initialized for queues: {queue_names}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        logger.info(f"Worker {self.worker_id} received {signal_name}, initiating graceful shutdown")
        self.shutdown_requested = True
    
    def start(self):
        """Start the worker with comprehensive monitoring"""
        try:
            logger.info(f"Starting worker {self.worker_id} for queues: {self.queue_names}")
            
            # Create worker instance
            worker = Worker(
                self.queues,
                connection=self.redis_conn,
                name=self.worker_id,
                default_result_ttl=self.ttl,
                default_worker_ttl=self.ttl
            )
            
            # Log worker startup metrics
            self._log_startup_metrics()
            
            # Start processing with monitoring
            self._monitor_and_work(worker)
            
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id} interrupted by user")
        except WorkerException as e:
            logger.error(f"Worker {self.worker_id} failed with RQ error: {e}")
            raise
        except Exception as e:
            logger.error(f"Worker {self.worker_id} failed with unexpected error: {e}")
            raise
        finally:
            self._cleanup()
    
    def _monitor_and_work(self, worker: Worker):
        """Main work loop with health monitoring"""
        logger.info(f"Worker {self.worker_id} starting job processing")
        
        # Performance tracking
        jobs_processed = 0
        last_health_check = time.time()
        health_check_interval = 60  # seconds
        
        try:
            while not self.shutdown_requested:
                try:
                    # Process jobs with timeout
                    result = worker.work(
                        burst=False,
                        logging_level=logging.getLevelName(logger.level),
                        job_timeout=self.timeout,
                        with_scheduler=True
                    )
                    
                    if result:
                        jobs_processed += 1
                        if jobs_processed % 10 == 0:
                            logger.info(f"Worker {self.worker_id} processed {jobs_processed} jobs")
                    
                    # Periodic health checks
                    current_time = time.time()
                    if current_time - last_health_check > health_check_interval:
                        self._perform_health_check(jobs_processed)
                        last_health_check = current_time
                    
                    # Brief pause to prevent tight loops
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} encountered error during processing: {e}")
                    time.sleep(1)  # Brief pause before retrying
                    
        except Exception as e:
            logger.error(f"Worker {self.worker_id} main loop failed: {e}")
            raise
        
        logger.info(f"Worker {self.worker_id} processed {jobs_processed} jobs total")
    
    def _perform_health_check(self, jobs_processed: int):
        """Perform comprehensive health check"""
        try:
            # Check Redis connectivity
            self.redis_conn.ping()
            
            # Calculate uptime
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Log health metrics
            logger.info(f"Worker {self.worker_id} health: OK, uptime: {uptime:.1f}s, jobs: {jobs_processed}")
            
            # Store health metrics in Redis for monitoring
            health_key = f"fingood:worker:health:{self.worker_id}"
            health_data = {
                'worker_id': self.worker_id,
                'queues': ','.join(self.queue_names),
                'uptime_seconds': uptime,
                'jobs_processed': jobs_processed,
                'last_seen': datetime.utcnow().isoformat(),
                'status': 'healthy'
            }
            
            self.redis_conn.hset(health_key, mapping=health_data)
            self.redis_conn.expire(health_key, 300)  # 5 minute expiry
            
        except Exception as e:
            logger.warning(f"Worker {self.worker_id} health check failed: {e}")
    
    def _log_startup_metrics(self):
        """Log comprehensive startup metrics"""
        try:
            # System information
            import platform
            import psutil
            
            system_info = {
                'hostname': platform.node(),
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'worker_id': self.worker_id,
                'queues': self.queue_names,
                'timeout': self.timeout,
                'ttl': self.ttl
            }
            
            logger.info(f"Worker startup metrics: {system_info}")
            
        except ImportError:
            logger.warning("psutil not available, skipping detailed system metrics")
        except Exception as e:
            logger.warning(f"Failed to collect startup metrics: {e}")
    
    def _cleanup(self):
        """Cleanup resources on shutdown"""
        try:
            logger.info(f"Worker {self.worker_id} performing cleanup")
            
            # Remove health status
            health_key = f"fingood:worker:health:{self.worker_id}"
            self.redis_conn.delete(health_key)
            
            # Calculate final metrics
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            logger.info(f"Worker {self.worker_id} shutdown complete, uptime: {uptime:.1f}s")
            
        except Exception as e:
            logger.error(f"Worker {self.worker_id} cleanup failed: {e}")

def start_multiple_workers(
    queue_names: List[str],
    worker_count: int,
    daemon: bool = False
) -> List[mp.Process]:
    """Start multiple worker processes"""
    processes = []
    
    logger.info(f"Starting {worker_count} workers for queues: {queue_names}")
    
    for i in range(worker_count):
        worker_id = f"worker-{os.getpid()}-{i+1}"
        
        def worker_target():
            # Setup logging in worker process
            setup_logging()
            worker = FinGoodWorker(queue_names, worker_id)
            worker.start()
        
        process = mp.Process(
            target=worker_target,
            name=worker_id,
            daemon=daemon
        )
        process.start()
        processes.append(process)
        
        logger.info(f"Started worker process {worker_id} (PID: {process.pid})")
    
    return processes

def wait_for_workers(processes: List[mp.Process]):
    """Wait for all worker processes to complete"""
    try:
        logger.info(f"Waiting for {len(processes)} worker processes")
        
        for process in processes:
            process.join()
            logger.info(f"Worker process {process.name} (PID: {process.pid}) completed")
            
    except KeyboardInterrupt:
        logger.info("Received interrupt, terminating workers")
        
        for process in processes:
            if process.is_alive():
                logger.info(f"Terminating worker process {process.name} (PID: {process.pid})")
                process.terminate()
                process.join(timeout=30)
                
                if process.is_alive():
                    logger.warning(f"Force killing worker process {process.name} (PID: {process.pid})")
                    process.kill()

def main():
    """Main entry point for worker startup"""
    parser = argparse.ArgumentParser(
        description="Start RQ workers for FinGood background job processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--queues',
        default='critical,high,default,low',
        help='Comma-separated list of queue names (default: all queues)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of worker processes to start (default: 1)'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run workers as daemon processes'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,
        help='Job timeout in seconds (default: 1800)'
    )
    
    parser.add_argument(
        '--ttl',
        type=int,
        default=3600,
        help='Worker TTL in seconds (default: 3600)'
    )
    
    parser.add_argument(
        '--log-level',
        default=os.getenv('LOG_LEVEL', 'INFO'),
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Parse queue names
    queue_names = [name.strip() for name in args.queues.split(',')]
    
    logger.info(f"FinGood RQ Worker Manager starting")
    logger.info(f"Configuration: queues={queue_names}, workers={args.workers}, "
                f"timeout={args.timeout}s, ttl={args.ttl}s")
    
    try:
        # Validate configuration
        if not settings.REDIS_URL:
            logger.error("REDIS_URL environment variable is required")
            sys.exit(1)
        
        # Test Redis connection
        try:
            redis_conn = redis.from_url(settings.REDIS_URL)
            redis_conn.ping()
            logger.info("Redis connection validated successfully")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            sys.exit(1)
        
        # Start workers
        if args.workers == 1:
            # Single worker mode
            worker = FinGoodWorker(queue_names, timeout=args.timeout, ttl=args.ttl)
            worker.start()
        else:
            # Multi-worker mode
            processes = start_multiple_workers(
                queue_names=queue_names,
                worker_count=args.workers,
                daemon=args.daemon
            )
            wait_for_workers(processes)
        
        logger.info("All workers completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Worker manager interrupted by user")
    except Exception as e:
        logger.error(f"Worker manager failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()