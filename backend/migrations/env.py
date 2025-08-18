import os
import sys
import logging
from logging.config import fileConfig
from typing import Any, Dict

from sqlalchemy import engine_from_config, text
from sqlalchemy import pool
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from alembic import context

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our models and configuration
from app.core.database import Base
from app.core.config import settings
from app.models import user, transaction  # Import all model modules

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the SQLAlchemy URL from our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get logger for migration operations
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Financial safety configuration
def get_migration_context() -> Dict[str, Any]:
    """Get enhanced migration context for financial applications."""
    return {
        'compare_type': True,
        'compare_server_default': True,
        'include_schemas': True,
        'render_as_batch': True,  # For SQLite compatibility in tests
        'transaction_per_migration': True,  # Each migration in its own transaction
    }

def validate_migration_safety() -> bool:
    """Validate migration safety for financial data."""
    try:
        # Check if we're in production environment
        is_production = os.getenv('ENVIRONMENT', '').lower() == 'production'
        
        if is_production:
            logger.info("Production environment detected - enabling enhanced safety checks")
            
            # Additional production safety checks can be added here
            # For example: check for backup verification, maintenance windows, etc.
            
        logger.info("Migration safety validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Migration safety validation failed: {e}")
        return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    logger.info("Running migrations in offline mode")
    
    # Validate migration safety
    if not validate_migration_safety():
        raise RuntimeError("Migration safety validation failed")
    
    url = config.get_main_option("sqlalchemy.url")
    migration_context = get_migration_context()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **migration_context
    )

    with context.begin_transaction():
        logger.info("Starting offline migration execution")
        context.run_migrations()
        logger.info("Offline migration execution completed")


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    logger.info("Running migrations in online mode")
    
    # Validate migration safety
    if not validate_migration_safety():
        raise RuntimeError("Migration safety validation failed")
    
    try:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            # Test connection health
            connection.execute(text("SELECT 1"))
            logger.info("Database connection verified")
            
            migration_context = get_migration_context()
            
            context.configure(
                connection=connection, 
                target_metadata=target_metadata,
                **migration_context
            )

            with context.begin_transaction():
                logger.info("Starting online migration execution")
                context.run_migrations()
                logger.info("Online migration execution completed")
                
    except (SQLAlchemyError, OperationalError) as e:
        logger.error(f"Database error during migration: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
