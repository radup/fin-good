#!/usr/bin/env python3
"""
FinGood Database Performance Management Script

Comprehensive tooling for monitoring and managing database performance optimizations.
Provides detailed analysis of index usage, query performance, and storage efficiency.

Usage:
    python scripts/database_performance.py --analyze-indexes
    python scripts/database_performance.py --monitor-queries
    python scripts/database_performance.py --check-fragmentation
    python scripts/database_performance.py --vacuum-analyze
    python scripts/database_performance.py --performance-report

Features:
- Index usage analysis and recommendations
- Query performance monitoring
- Database fragmentation detection
- Automated maintenance operations
- Performance benchmarking
- Comprehensive reporting

"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import psutil
import json

# Add project root to path
sys.path.append('/Users/ra/work/fin-good/backend')

from app.core.config import settings
from app.core.database import get_db_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_performance.log')
    ]
)
logger = logging.getLogger(__name__)

class DatabasePerformanceAnalyzer:
    """
    Comprehensive database performance analysis and optimization tool.
    """
    
    def __init__(self):
        """Initialize the performance analyzer with database connection."""
        try:
            self.engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                echo=False
            )
            self.SessionLocal = sessionmaker(bind=self.engine)
            logger.info("Database performance analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            sys.exit(1)
    
    def check_database_health(self) -> Dict:
        """Check overall database health and connectivity."""
        try:
            health = get_db_health()
            logger.info(f"Database health check: {health['status']}")
            return health
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def analyze_index_usage(self) -> List[Dict]:
        """
        Analyze index usage statistics and provide optimization recommendations.
        """
        logger.info("Analyzing database index usage...")
        
        with self.engine.connect() as conn:
            # Check if we're on PostgreSQL
            if conn.dialect.name != 'postgresql':
                logger.warning("Index analysis only supported on PostgreSQL")
                return []
            
            # Query index usage statistics
            index_usage_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
                    pg_relation_size(indexrelid) as index_size_bytes,
                    CASE 
                        WHEN idx_scan = 0 THEN 'UNUSED'
                        WHEN idx_scan < 100 THEN 'LOW_USAGE'
                        WHEN idx_scan < 1000 THEN 'MODERATE_USAGE'
                        ELSE 'HIGH_USAGE'
                    END as usage_category
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC, pg_relation_size(indexrelid) DESC
            """)
            
            results = conn.execute(index_usage_query).fetchall()
            
            index_analysis = []
            for row in results:
                analysis = {
                    'schema': row.schemaname,
                    'table': row.tablename,
                    'index': row.indexname,
                    'scans': row.idx_scan,
                    'tuples_read': row.idx_tup_read,
                    'tuples_fetched': row.idx_tup_fetch,
                    'size': row.index_size,
                    'size_bytes': row.index_size_bytes,
                    'usage_category': row.usage_category,
                    'efficiency': (row.idx_tup_fetch / max(row.idx_tup_read, 1)) * 100 if row.idx_tup_read > 0 else 0
                }
                
                # Add recommendations
                if analysis['usage_category'] == 'UNUSED':
                    analysis['recommendation'] = 'Consider dropping this unused index'
                elif analysis['usage_category'] == 'LOW_USAGE' and analysis['size_bytes'] > 1000000:
                    analysis['recommendation'] = 'Monitor usage - consider dropping if consistently low'
                elif analysis['efficiency'] < 10:
                    analysis['recommendation'] = 'Low efficiency index - review index design'
                else:
                    analysis['recommendation'] = 'Index appears to be performing well'
                
                index_analysis.append(analysis)
            
            logger.info(f"Analyzed {len(index_analysis)} indexes")
            return index_analysis
    
    def monitor_slow_queries(self, duration_threshold: float = 1.0) -> List[Dict]:
        """
        Monitor and analyze slow queries.
        """
        logger.info(f"Monitoring queries slower than {duration_threshold}s...")
        
        with self.engine.connect() as conn:
            if conn.dialect.name != 'postgresql':
                logger.warning("Query monitoring only supported on PostgreSQL")
                return []
            
            # Enable query statistics if not already enabled
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
            except Exception as e:
                logger.warning(f"Could not enable pg_stat_statements: {e}")
                return []
            
            slow_queries_query = text("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    stddev_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_exec_time > :threshold
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """)
            
            results = conn.execute(slow_queries_query, {"threshold": duration_threshold * 1000}).fetchall()
            
            slow_queries = []
            for row in results:
                query_analysis = {
                    'query': row.query[:200] + '...' if len(row.query) > 200 else row.query,
                    'calls': row.calls,
                    'total_time_ms': row.total_exec_time,
                    'mean_time_ms': row.mean_exec_time,
                    'stddev_time_ms': row.stddev_exec_time,
                    'rows_avg': row.rows / max(row.calls, 1),
                    'cache_hit_percent': row.hit_percent or 0
                }
                
                # Add performance recommendations
                if query_analysis['mean_time_ms'] > 5000:
                    query_analysis['recommendation'] = 'CRITICAL: Query needs immediate optimization'
                elif query_analysis['mean_time_ms'] > 1000:
                    query_analysis['recommendation'] = 'HIGH: Consider adding indexes or optimizing query'
                elif query_analysis['cache_hit_percent'] < 90:
                    query_analysis['recommendation'] = 'MODERATE: Low cache hit ratio - check buffer configuration'
                else:
                    query_analysis['recommendation'] = 'MONITOR: Query performance acceptable but monitor trends'
                
                slow_queries.append(query_analysis)
            
            logger.info(f"Found {len(slow_queries)} slow queries")
            return slow_queries
    
    def check_table_bloat(self) -> List[Dict]:
        """
        Check for table bloat and fragmentation.
        """
        logger.info("Checking table bloat and fragmentation...")
        
        with self.engine.connect() as conn:
            if conn.dialect.name != 'postgresql':
                logger.warning("Bloat analysis only supported on PostgreSQL")
                return []
            
            bloat_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup,
                    CASE 
                        WHEN n_live_tup > 0 THEN (n_dead_tup::float / n_live_tup::float) * 100
                        ELSE 0
                    END as dead_tuple_percent,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_dead_tup DESC
            """)
            
            results = conn.execute(bloat_query).fetchall()
            
            bloat_analysis = []
            for row in results:
                analysis = {
                    'schema': row.schemaname,
                    'table': row.tablename,
                    'size': row.size,
                    'size_bytes': row.size_bytes,
                    'live_tuples': row.n_live_tup,
                    'dead_tuples': row.n_dead_tup,
                    'dead_tuple_percent': row.dead_tuple_percent,
                    'last_vacuum': row.last_vacuum,
                    'last_autovacuum': row.last_autovacuum,
                    'last_analyze': row.last_analyze,
                    'last_autoanalyze': row.last_autoanalyze
                }
                
                # Add maintenance recommendations
                if analysis['dead_tuple_percent'] > 20:
                    analysis['recommendation'] = 'URGENT: High bloat detected - run VACUUM immediately'
                elif analysis['dead_tuple_percent'] > 10:
                    analysis['recommendation'] = 'HIGH: Moderate bloat - schedule VACUUM soon'
                elif not analysis['last_analyze'] or (datetime.now() - analysis['last_analyze']).days > 7:
                    analysis['recommendation'] = 'MODERATE: Table needs ANALYZE for query planning'
                else:
                    analysis['recommendation'] = 'GOOD: Table maintenance up to date'
                
                bloat_analysis.append(analysis)
            
            logger.info(f"Analyzed bloat for {len(bloat_analysis)} tables")
            return bloat_analysis
    
    def run_vacuum_analyze(self, table_name: Optional[str] = None) -> Dict:
        """
        Run VACUUM ANALYZE on specified table or all tables.
        """
        logger.info(f"Running VACUUM ANALYZE on {'all tables' if not table_name else table_name}...")
        
        results = {
            'started_at': datetime.now(),
            'tables_processed': [],
            'errors': []
        }
        
        with self.engine.connect() as conn:
            if conn.dialect.name != 'postgresql':
                logger.warning("VACUUM ANALYZE only supported on PostgreSQL")
                return results
            
            try:
                # Set autocommit for VACUUM operations
                conn = conn.execution_options(autocommit=True)
                
                if table_name:
                    tables = [table_name]
                else:
                    # Get all user tables
                    table_query = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                    tables = [row.tablename for row in conn.execute(table_query).fetchall()]
                
                for table in tables:
                    try:
                        start_time = time.time()
                        conn.execute(text(f"VACUUM ANALYZE {table}"))
                        duration = time.time() - start_time
                        
                        results['tables_processed'].append({
                            'table': table,
                            'duration_seconds': duration,
                            'status': 'success'
                        })
                        logger.info(f"VACUUM ANALYZE completed for {table} in {duration:.2f}s")
                        
                    except Exception as e:
                        error_msg = f"Failed to VACUUM ANALYZE {table}: {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
            except Exception as e:
                error_msg = f"VACUUM ANALYZE operation failed: {e}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        results['completed_at'] = datetime.now()
        results['total_duration'] = (results['completed_at'] - results['started_at']).total_seconds()
        
        logger.info(f"VACUUM ANALYZE completed. Processed {len(results['tables_processed'])} tables")
        return results
    
    def generate_performance_report(self) -> Dict:
        """
        Generate comprehensive performance report.
        """
        logger.info("Generating comprehensive performance report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_health': self.check_database_health(),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
                'disk_usage': {}
            }
        }
        
        # Add disk usage for database directory
        try:
            disk_usage = psutil.disk_usage('/')
            report['system_info']['disk_usage'] = {
                'total_gb': disk_usage.total / (1024**3),
                'used_gb': disk_usage.used / (1024**3),
                'free_gb': disk_usage.free / (1024**3),
                'percent_used': (disk_usage.used / disk_usage.total) * 100
            }
        except Exception as e:
            logger.warning(f"Could not get disk usage: {e}")
        
        # Collect performance data
        report['index_analysis'] = self.analyze_index_usage()
        report['slow_queries'] = self.monitor_slow_queries()
        report['table_bloat'] = self.check_table_bloat()
        
        # Calculate summary statistics
        if report['index_analysis']:
            unused_indexes = [idx for idx in report['index_analysis'] if idx['usage_category'] == 'UNUSED']
            report['summary'] = {
                'total_indexes': len(report['index_analysis']),
                'unused_indexes': len(unused_indexes),
                'total_index_size_mb': sum(idx['size_bytes'] for idx in report['index_analysis']) / (1024**2),
                'wasted_space_mb': sum(idx['size_bytes'] for idx in unused_indexes) / (1024**2)
            }
        
        if report['slow_queries']:
            report['summary']['slow_queries_count'] = len(report['slow_queries'])
            report['summary']['avg_query_time_ms'] = sum(q['mean_time_ms'] for q in report['slow_queries']) / len(report['slow_queries'])
        
        if report['table_bloat']:
            high_bloat_tables = [t for t in report['table_bloat'] if t['dead_tuple_percent'] > 10]
            report['summary']['high_bloat_tables'] = len(high_bloat_tables)
        
        logger.info("Performance report generated successfully")
        return report
    
    def export_report(self, report: Dict, filename: str = None) -> str:
        """Export performance report to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fingood_performance_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Performance report exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return ""

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description='FinGood Database Performance Management')
    parser.add_argument('--analyze-indexes', action='store_true', help='Analyze index usage')
    parser.add_argument('--monitor-queries', action='store_true', help='Monitor slow queries')
    parser.add_argument('--check-fragmentation', action='store_true', help='Check table fragmentation')
    parser.add_argument('--vacuum-analyze', action='store_true', help='Run VACUUM ANALYZE')
    parser.add_argument('--performance-report', action='store_true', help='Generate full performance report')
    parser.add_argument('--table', type=str, help='Specific table for operations')
    parser.add_argument('--export', action='store_true', help='Export results to JSON file')
    parser.add_argument('--threshold', type=float, default=1.0, help='Query duration threshold in seconds')
    
    args = parser.parse_args()
    
    if not any([args.analyze_indexes, args.monitor_queries, args.check_fragmentation, 
                args.vacuum_analyze, args.performance_report]):
        parser.print_help()
        sys.exit(1)
    
    analyzer = DatabasePerformanceAnalyzer()
    
    try:
        if args.analyze_indexes:
            results = analyzer.analyze_index_usage()
            print("\n=== INDEX USAGE ANALYSIS ===")
            for idx in results:
                print(f"Table: {idx['table']}, Index: {idx['index']}, "
                      f"Scans: {idx['scans']}, Size: {idx['size']}, "
                      f"Category: {idx['usage_category']}")
                print(f"  Recommendation: {idx['recommendation']}\n")
        
        if args.monitor_queries:
            results = analyzer.monitor_slow_queries(args.threshold)
            print(f"\n=== SLOW QUERIES (>{args.threshold}s) ===")
            for query in results:
                print(f"Query: {query['query']}")
                print(f"  Avg Time: {query['mean_time_ms']:.2f}ms, Calls: {query['calls']}")
                print(f"  Recommendation: {query['recommendation']}\n")
        
        if args.check_fragmentation:
            results = analyzer.check_table_bloat()
            print("\n=== TABLE BLOAT ANALYSIS ===")
            for table in results:
                print(f"Table: {table['table']}, Size: {table['size']}, "
                      f"Dead Tuples: {table['dead_tuple_percent']:.1f}%")
                print(f"  Recommendation: {table['recommendation']}\n")
        
        if args.vacuum_analyze:
            results = analyzer.run_vacuum_analyze(args.table)
            print("\n=== VACUUM ANALYZE RESULTS ===")
            print(f"Duration: {results['total_duration']:.2f}s")
            print(f"Tables processed: {len(results['tables_processed'])}")
            if results['errors']:
                print(f"Errors: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"  - {error}")
        
        if args.performance_report:
            report = analyzer.generate_performance_report()
            print("\n=== PERFORMANCE REPORT SUMMARY ===")
            if 'summary' in report:
                summary = report['summary']
                print(f"Total Indexes: {summary.get('total_indexes', 'N/A')}")
                print(f"Unused Indexes: {summary.get('unused_indexes', 'N/A')}")
                print(f"Total Index Size: {summary.get('total_index_size_mb', 0):.1f} MB")
                print(f"Wasted Space: {summary.get('wasted_space_mb', 0):.1f} MB")
                print(f"Slow Queries: {summary.get('slow_queries_count', 'N/A')}")
                print(f"High Bloat Tables: {summary.get('high_bloat_tables', 'N/A')}")
            
            if args.export:
                filename = analyzer.export_report(report)
                if filename:
                    print(f"\nFull report exported to: {filename}")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()