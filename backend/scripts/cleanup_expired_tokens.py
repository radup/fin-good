#!/usr/bin/env python3
"""
Password Reset Token Cleanup Script

This script cleans up expired password reset tokens from the database.
It should be run as a scheduled job (e.g., cron job) to maintain database hygiene
and prevent token table from growing too large.

Usage:
    python scripts/cleanup_expired_tokens.py [--dry-run] [--verbose]
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.services.password_reset_service import get_password_reset_service
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cleanup_expired_tokens(dry_run: bool = False, verbose: bool = False) -> int:
    """
    Clean up expired password reset tokens.
    
    Args:
        dry_run: If True, only count tokens without deleting them
        verbose: If True, provide detailed logging
        
    Returns:
        int: Number of tokens that were (or would be) cleaned up
    """
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Get password reset service
        reset_service = get_password_reset_service()
        
        if dry_run:
            # Count expired tokens without deleting them
            from app.models.user import PasswordResetToken
            now = datetime.utcnow()
            
            expired_count = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at <= now
            ).count()
            
            if verbose:
                logger.info(f"DRY RUN: Would clean up {expired_count} expired tokens")
            
            return expired_count
        else:
            # Actually clean up expired tokens
            cleaned_count = reset_service.cleanup_expired_tokens_batch(db)
            
            if verbose or cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired password reset tokens")
            
            return cleaned_count
            
    except Exception as e:
        logger.error(f"Error during token cleanup: {e}")
        return 0
    finally:
        # Close database session
        try:
            db.close()
        except:
            pass


def get_token_statistics() -> dict:
    """Get statistics about password reset tokens."""
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        from app.models.user import PasswordResetToken
        now = datetime.utcnow()
        
        # Get various token counts
        total_tokens = db.query(PasswordResetToken).count()
        
        active_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at > now,
            PasswordResetToken.is_used == False
        ).count()
        
        expired_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at <= now
        ).count()
        
        used_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.is_used == True
        ).count()
        
        # Get oldest and newest token dates
        oldest_token = db.query(PasswordResetToken).order_by(
            PasswordResetToken.created_at.asc()
        ).first()
        
        newest_token = db.query(PasswordResetToken).order_by(
            PasswordResetToken.created_at.desc()
        ).first()
        
        stats = {
            'total_tokens': total_tokens,
            'active_tokens': active_tokens,
            'expired_tokens': expired_tokens,
            'used_tokens': used_tokens,
            'oldest_token_date': oldest_token.created_at if oldest_token else None,
            'newest_token_date': newest_token.created_at if newest_token else None
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting token statistics: {e}")
        return {}
    finally:
        try:
            db.close()
        except:
            pass


def main():
    """Main function to handle command line arguments and run cleanup."""
    parser = argparse.ArgumentParser(
        description="Clean up expired password reset tokens"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be cleaned up without actually doing it'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show token statistics'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Show statistics if requested
        if args.stats:
            logger.info("Getting password reset token statistics...")
            stats = get_token_statistics()
            
            if stats:
                logger.info("=== Password Reset Token Statistics ===")
                logger.info(f"Total tokens: {stats.get('total_tokens', 0)}")
                logger.info(f"Active tokens: {stats.get('active_tokens', 0)}")
                logger.info(f"Expired tokens: {stats.get('expired_tokens', 0)}")
                logger.info(f"Used tokens: {stats.get('used_tokens', 0)}")
                
                if stats.get('oldest_token_date'):
                    logger.info(f"Oldest token: {stats['oldest_token_date']}")
                if stats.get('newest_token_date'):
                    logger.info(f"Newest token: {stats['newest_token_date']}")
                logger.info("=" * 40)
            else:
                logger.warning("Could not retrieve token statistics")
        
        # Perform cleanup
        if args.dry_run:
            logger.info("Starting DRY RUN cleanup of expired password reset tokens...")
        else:
            logger.info("Starting cleanup of expired password reset tokens...")
        
        cleaned_count = cleanup_expired_tokens(
            dry_run=args.dry_run,
            verbose=args.verbose
        )
        
        if args.dry_run:
            logger.info(f"DRY RUN complete: {cleaned_count} tokens would be cleaned up")
        else:
            logger.info(f"Cleanup complete: {cleaned_count} tokens cleaned up")
        
        # Exit with appropriate code
        sys.exit(0 if cleaned_count >= 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()