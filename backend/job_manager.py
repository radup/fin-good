#!/usr/bin/env python3
"""
Job Management CLI for FinGood Background Jobs

This CLI provides comprehensive job management capabilities for production environments.
It allows administrators to monitor, manage, and troubleshoot background jobs.

Features:
- List and filter jobs by status, user, date range
- View detailed job information and logs
- Cancel, retry, or restart jobs
- Queue statistics and health monitoring
- Bulk operations for job management
- Export job data for analysis
- Worker monitoring and management

Usage:
    python job_manager.py status                           # Show queue status
    python job_manager.py list --status processing         # List processing jobs
    python job_manager.py list --user user@example.com     # List jobs for user
    python job_manager.py show <job_id>                    # Show job details
    python job_manager.py cancel <job_id>                  # Cancel a job
    python job_manager.py retry <job_id>                   # Retry a failed job
    python job_manager.py cleanup --older-than 7d          # Cleanup old jobs
    python job_manager.py workers                          # Show worker status
    python job_manager.py export --format csv              # Export job data

Environment Variables:
    REDIS_URL: Redis connection URL (required)
    DATABASE_URL: Database connection URL (for user lookups)
"""

import argparse
import asyncio
import csv
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

import redis
from rq import Queue, Worker, Job
from rq.job import JobStatus
from tabulate import tabulate

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.core.background_jobs import job_manager, JobState, JobType, JobPriority
from app.core.logging_config import setup_logging

# Setup logging
logger = logging.getLogger(__name__)

class JobManagerCLI:
    """
    Comprehensive CLI for managing FinGood background jobs.
    """
    
    def __init__(self):
        """Initialize the job manager CLI"""
        self.redis_conn = None
        self.job_manager = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis and initialize job manager"""
        try:
            self.redis_conn = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=30
            )
            self.redis_conn.ping()
            
            # Initialize job manager
            self.job_manager = job_manager
            
            logger.info("Connected to Redis and initialized job manager")
            
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            print(f"❌ Error: Failed to connect to Redis: {e}")
            print("   Make sure Redis is running and REDIS_URL is correct")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize job manager: {e}")
            print(f"❌ Error: Failed to initialize job manager: {e}")
            sys.exit(1)
    
    async def show_status(self):
        """Show comprehensive queue and system status"""
        try:
            print("🔄 FinGood Background Job System Status\n")
            
            # Get queue statistics
            queue_stats = self.job_manager.get_queue_stats()
            
            if 'error' in queue_stats:
                print(f"❌ Error getting queue stats: {queue_stats['error']}")
                return
            
            # Queue status table
            queue_data = []
            total_queued = 0
            total_processing = 0
            total_failed = 0
            
            for priority, stats in queue_stats.get('queues', {}).items():
                queue_data.append([
                    priority.upper(),
                    stats.get('length', 0),
                    stats.get('started_count', 0),
                    stats.get('failed_count', 0),
                    stats.get('finished_count', 0)
                ])
                total_queued += stats.get('length', 0)
                total_processing += stats.get('started_count', 0)
                total_failed += stats.get('failed_count', 0)
            
            print("📊 Queue Status:")
            print(tabulate(
                queue_data,
                headers=['Priority', 'Queued', 'Processing', 'Failed', 'Completed'],
                tablefmt='grid'
            ))
            
            # Summary
            print(f"\n📈 Summary:")
            print(f"   Total Queued: {total_queued}")
            print(f"   Total Processing: {total_processing}")
            print(f"   Total Failed: {total_failed}")
            
            # Redis info
            redis_info = queue_stats.get('redis_info', {})
            print(f"\n💾 Redis Status:")
            print(f"   Memory Used: {redis_info.get('used_memory', 'N/A')}")
            print(f"   Connected Clients: {redis_info.get('connected_clients', 'N/A')}")
            
            # Worker status
            await self._show_worker_status()
            
        except Exception as e:
            logger.error(f"Failed to show status: {e}")
            print(f"❌ Error: {e}")
    
    async def _show_worker_status(self):
        """Show worker status information"""
        try:
            print(f"\n👷 Worker Status:")
            
            # Get worker health information from Redis
            worker_keys = self.redis_conn.keys("fingood:worker:health:*")
            
            if not worker_keys:
                print("   No active workers found")
                return
            
            worker_data = []
            for key in worker_keys:
                health = self.redis_conn.hgetall(key)
                if health:
                    worker_data.append([
                        health.get('worker_id', 'Unknown'),
                        health.get('queues', 'Unknown'),
                        health.get('uptime_seconds', '0'),
                        health.get('jobs_processed', '0'),
                        health.get('status', 'Unknown'),
                        health.get('last_seen', 'Unknown')
                    ])
            
            if worker_data:
                print(tabulate(
                    worker_data,
                    headers=['Worker ID', 'Queues', 'Uptime (s)', 'Jobs', 'Status', 'Last Seen'],
                    tablefmt='grid'
                ))
            else:
                print("   No worker health data available")
                
        except Exception as e:
            logger.warning(f"Failed to get worker status: {e}")
            print(f"   Warning: Could not retrieve worker status: {e}")
    
    async def list_jobs(
        self,
        status_filter: Optional[str] = None,
        user_filter: Optional[str] = None,
        limit: int = 50,
        since: Optional[datetime] = None
    ):
        """List jobs with optional filtering"""
        try:
            print(f"📋 Jobs List (limit: {limit})\n")
            
            # For this demo, we'll show jobs from all users
            # In a real implementation, you'd query the database for user IDs
            
            if user_filter:
                print(f"🔍 Filtering by user: {user_filter}")
                # TODO: Look up user ID from email
                user_jobs = await self.job_manager.get_user_jobs(user_filter, limit=limit)
                jobs_to_show = user_jobs
            else:
                # Get jobs from Redis keys (simplified approach)
                job_keys = self.redis_conn.keys("fingood:job:progress:*")
                jobs_to_show = []
                
                for key in job_keys[:limit]:
                    job_id = key.split(':')[-1]
                    job_progress = await self.job_manager.get_job_status(job_id)
                    if job_progress:
                        jobs_to_show.append(job_progress)
            
            # Apply status filter
            if status_filter:
                try:
                    filter_state = JobState(status_filter.lower())
                    jobs_to_show = [job for job in jobs_to_show if job.state == filter_state]
                except ValueError:
                    print(f"❌ Invalid status filter: {status_filter}")
                    print(f"   Valid statuses: {', '.join([s.value for s in JobState])}")
                    return
            
            # Apply date filter
            if since:
                jobs_to_show = [job for job in jobs_to_show if job.created_at >= since]
            
            if not jobs_to_show:
                print("No jobs found matching the criteria")
                return
            
            # Format job data
            job_data = []
            for job in jobs_to_show:
                elapsed = (datetime.utcnow() - job.created_at).total_seconds()
                job_data.append([
                    job.job_id[:8] + "...",  # Truncated job ID
                    job.job_type.value,
                    job.state.value,
                    f"{job.progress_percentage:.1f}%",
                    job.current_step,
                    job.user_id[:8] + "..." if len(job.user_id) > 8 else job.user_id,
                    f"{elapsed:.0f}s",
                    job.details.get('filename', 'N/A') if job.details else 'N/A'
                ])
            
            print(tabulate(
                job_data,
                headers=['Job ID', 'Type', 'Status', 'Progress', 'Step', 'User', 'Age', 'File'],
                tablefmt='grid'
            ))
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            print(f"❌ Error: {e}")
    
    async def show_job(self, job_id: str):
        """Show detailed information about a specific job"""
        try:
            print(f"🔍 Job Details: {job_id}\n")
            
            job_progress = await self.job_manager.get_job_status(job_id)
            
            if not job_progress:
                print(f"❌ Job not found: {job_id}")
                return
            
            # Basic job information
            print("📋 Basic Information:")
            print(f"   Job ID: {job_progress.job_id}")
            print(f"   Type: {job_progress.job_type.value}")
            print(f"   Status: {job_progress.state.value}")
            print(f"   Progress: {job_progress.progress_percentage:.1f}%")
            print(f"   Current Step: {job_progress.current_step}")
            print(f"   Message: {job_progress.message}")
            print(f"   User ID: {job_progress.user_id}")
            
            # Timing information
            print(f"\n⏱️  Timing:")
            print(f"   Created: {job_progress.created_at}")
            print(f"   Updated: {job_progress.updated_at}")
            if job_progress.started_at:
                print(f"   Started: {job_progress.started_at}")
            if job_progress.completed_at:
                print(f"   Completed: {job_progress.completed_at}")
            
            elapsed = (datetime.utcnow() - job_progress.created_at).total_seconds()
            print(f"   Elapsed: {elapsed:.1f} seconds")
            
            # Retry information
            print(f"\n🔄 Retry Information:")
            print(f"   Retry Count: {job_progress.retry_count}")
            print(f"   Max Retries: {job_progress.max_retries}")
            
            # Job details
            if job_progress.details:
                print(f"\n📊 Job Details:")
                for key, value in job_progress.details.items():
                    print(f"   {key}: {value}")
            
            # Error information
            if job_progress.error_info:
                print(f"\n❌ Error Information:")
                for key, value in job_progress.error_info.items():
                    print(f"   {key}: {value}")
            
            # Try to get RQ job information
            try:
                rq_job = Job.fetch(job_id, connection=self.redis_conn)
                print(f"\n🔧 RQ Job Information:")
                print(f"   RQ Status: {rq_job.status}")
                print(f"   Queue: {rq_job.origin}")
                if rq_job.exc_info:
                    print(f"   Exception: {rq_job.exc_info}")
            except Exception:
                print(f"\n🔧 RQ Job Information: Not available")
            
        except Exception as e:
            logger.error(f"Failed to show job: {e}")
            print(f"❌ Error: {e}")
    
    async def cancel_job(self, job_id: str, force: bool = False):
        """Cancel a job"""
        try:
            print(f"⏹️  Cancelling job: {job_id}")
            
            job_progress = await self.job_manager.get_job_status(job_id)
            
            if not job_progress:
                print(f"❌ Job not found: {job_id}")
                return
            
            if not force and job_progress.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
                print(f"❌ Cannot cancel job in {job_progress.state.value} state")
                print("   Use --force to force cancellation")
                return
            
            # For CLI, we don't have a specific user, so we'll use the job's user
            success = await self.job_manager.cancel_job(job_id, job_progress.user_id)
            
            if success:
                print(f"✅ Job {job_id} cancelled successfully")
            else:
                print(f"❌ Failed to cancel job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            print(f"❌ Error: {e}")
    
    async def cleanup_jobs(self, older_than_days: int = 7, dry_run: bool = False):
        """Clean up old job records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            print(f"🧹 Cleaning up jobs older than {older_than_days} days (before {cutoff_date})")
            
            if dry_run:
                print("   DRY RUN - No changes will be made")
            
            # Get all job progress keys
            job_keys = self.redis_conn.keys("fingood:job:progress:*")
            cleaned_count = 0
            
            for key in job_keys:
                try:
                    job_data = self.redis_conn.get(key)
                    if job_data:
                        job_info = json.loads(job_data)
                        created_at = datetime.fromisoformat(job_info.get('created_at'))
                        
                        if created_at < cutoff_date:
                            if not dry_run:
                                # Delete job progress
                                self.redis_conn.delete(key)
                                
                                # Remove from user job sets
                                user_id = job_info.get('user_id')
                                if user_id:
                                    user_jobs_key = f"fingood:user:jobs:{user_id}"
                                    job_id = job_info.get('job_id')
                                    if job_id:
                                        self.redis_conn.srem(user_jobs_key, job_id)
                            
                            cleaned_count += 1
                            
                except Exception as e:
                    logger.warning(f"Failed to process job key {key}: {e}")
            
            if dry_run:
                print(f"   Would clean up {cleaned_count} jobs")
            else:
                print(f"✅ Cleaned up {cleaned_count} jobs")
            
        except Exception as e:
            logger.error(f"Failed to cleanup jobs: {e}")
            print(f"❌ Error: {e}")
    
    async def export_jobs(self, format_type: str = 'csv', output_file: Optional[str] = None):
        """Export job data for analysis"""
        try:
            print(f"📤 Exporting jobs in {format_type} format")
            
            # Get all jobs
            job_keys = self.redis_conn.keys("fingood:job:progress:*")
            jobs_data = []
            
            for key in job_keys:
                try:
                    job_data = self.redis_conn.get(key)
                    if job_data:
                        job_info = json.loads(job_data)
                        jobs_data.append(job_info)
                except Exception as e:
                    logger.warning(f"Failed to process job key {key}: {e}")
            
            if not jobs_data:
                print("No jobs found to export")
                return
            
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"fingood_jobs_{timestamp}.{format_type}"
            
            if format_type == 'csv':
                await self._export_csv(jobs_data, output_file)
            elif format_type == 'json':
                await self._export_json(jobs_data, output_file)
            else:
                print(f"❌ Unsupported format: {format_type}")
                return
            
            print(f"✅ Exported {len(jobs_data)} jobs to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to export jobs: {e}")
            print(f"❌ Error: {e}")
    
    async def _export_csv(self, jobs_data: List[Dict], output_file: str):
        """Export jobs data to CSV"""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'job_id', 'job_type', 'state', 'progress_percentage',
                'current_step', 'message', 'user_id', 'created_at',
                'updated_at', 'retry_count', 'max_retries'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for job in jobs_data:
                # Extract only the fields we want
                row = {field: job.get(field, '') for field in fieldnames}
                writer.writerow(row)
    
    async def _export_json(self, jobs_data: List[Dict], output_file: str):
        """Export jobs data to JSON"""
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(jobs_data, jsonfile, indent=2, default=str)

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FinGood Job Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show queue and worker status')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List jobs')
    list_parser.add_argument('--status', help='Filter by job status')
    list_parser.add_argument('--user', help='Filter by user email')
    list_parser.add_argument('--limit', type=int, default=50, help='Limit number of results')
    list_parser.add_argument('--since', help='Show jobs since date (YYYY-MM-DD)')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show job details')
    show_parser.add_argument('job_id', help='Job ID to show')
    
    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a job')
    cancel_parser.add_argument('job_id', help='Job ID to cancel')
    cancel_parser.add_argument('--force', action='store_true', help='Force cancellation')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old jobs')
    cleanup_parser.add_argument('--older-than', type=int, default=7, help='Days old (default: 7)')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export job data')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Export format')
    export_parser.add_argument('--output', help='Output file name')
    
    # Workers command
    workers_parser = subparsers.add_parser('workers', help='Show worker status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging()
    
    # Initialize CLI
    cli = JobManagerCLI()
    
    try:
        if args.command == 'status':
            await cli.show_status()
        
        elif args.command == 'list':
            since_date = None
            if args.since:
                try:
                    since_date = datetime.strptime(args.since, '%Y-%m-%d')
                except ValueError:
                    print(f"❌ Invalid date format: {args.since}. Use YYYY-MM-DD")
                    return
            
            await cli.list_jobs(
                status_filter=args.status,
                user_filter=args.user,
                limit=args.limit,
                since=since_date
            )
        
        elif args.command == 'show':
            await cli.show_job(args.job_id)
        
        elif args.command == 'cancel':
            await cli.cancel_job(args.job_id, force=args.force)
        
        elif args.command == 'cleanup':
            await cli.cleanup_jobs(older_than_days=args.older_than, dry_run=args.dry_run)
        
        elif args.command == 'export':
            await cli.export_jobs(format_type=args.format, output_file=args.output)
        
        elif args.command == 'workers':
            await cli._show_worker_status()
        
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
    except Exception as e:
        logger.error(f"CLI command failed: {e}")
        print(f"❌ Command failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    # Install required package if missing
    try:
        import tabulate
    except ImportError:
        print("❌ Missing required package: tabulate")
        print("   Install with: pip install tabulate")
        sys.exit(1)
    
    asyncio.run(main())