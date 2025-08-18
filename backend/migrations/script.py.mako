"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

FINANCIAL SAFETY NOTICE:
This migration affects financial data. Ensure proper backup and testing procedures
are followed before applying to production. All changes must be reversible.

ROLLBACK STRATEGY:
- Test rollback procedures in staging environment
- Verify data integrity after rollback
- Document any manual steps required for rollback

"""
from typing import Sequence, Union
import logging

from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError, OperationalError
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

# Configure logging for this migration
logger = logging.getLogger(__name__)


def validate_data_integrity() -> bool:
    """
    Validate financial data integrity before and after migration.
    This function should be customized for each migration's specific requirements.
    """
    try:
        # Add specific validation logic here
        # Example: Check for orphaned records, constraint violations, etc.
        logger.info("Data integrity validation passed")
        return True
    except Exception as e:
        logger.error(f"Data integrity validation failed: {e}")
        return False


def upgrade() -> None:
    """Apply the migration changes."""
    logger.info(f"Starting migration upgrade: ${message}")
    
    try:
        # Validate data integrity before migration
        if not validate_data_integrity():
            raise RuntimeError("Pre-migration data integrity check failed")
        
        ${upgrades if upgrades else "# Add your upgrade logic here\n        pass"}
        
        # Validate data integrity after migration
        if not validate_data_integrity():
            raise RuntimeError("Post-migration data integrity check failed")
        
        logger.info(f"Migration upgrade completed successfully: ${message}")
        
    except (SQLAlchemyError, OperationalError) as e:
        logger.error(f"Database error in migration upgrade: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in migration upgrade: {e}")
        raise


def downgrade() -> None:
    """Rollback the migration changes."""
    logger.info(f"Starting migration downgrade: ${message}")
    
    try:
        # Validate data integrity before rollback
        if not validate_data_integrity():
            raise RuntimeError("Pre-rollback data integrity check failed")
        
        ${downgrades if downgrades else "# Add your downgrade logic here\n        pass"}
        
        # Validate data integrity after rollback
        if not validate_data_integrity():
            raise RuntimeError("Post-rollback data integrity check failed")
        
        logger.info(f"Migration downgrade completed successfully: ${message}")
        
    except (SQLAlchemyError, OperationalError) as e:
        logger.error(f"Database error in migration downgrade: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in migration downgrade: {e}")
        raise
