from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
import sys
import time
import logging
from app.core.config import settings

# Configure logging for database operations
logger = logging.getLogger(__name__)

def create_database_engine():
    """Create database engine with comprehensive error handling and security features."""
    try:
        # Enhanced security and reliability settings for financial applications
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=300,    # Recycle connections every 5 minutes
            pool_size=10,        # Maximum number of connections in pool
            max_overflow=20,     # Additional connections when pool is full
            pool_timeout=30,     # Timeout for getting connection from pool
            echo=settings.DEBUG, # Log SQL queries in debug mode
            # Security: Disable autocommit to ensure transaction integrity
            isolation_level="READ_COMMITTED",
            # Enable connection health checks
            connect_args={
                "connect_timeout": 10,  # Connection timeout in seconds
                "application_name": "FinGood",  # Identify our application
            } if settings.DATABASE_URL.startswith('postgresql') else {}
        )
        
        # Test database connection on startup
        test_database_connection(engine)
        
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {str(e)}")
        print(f"\n❌ DATABASE CONNECTION FAILED: {str(e)}\n", file=sys.stderr)
        print("🔍 Common issues:", file=sys.stderr)
        print("  • Check DATABASE_URL environment variable", file=sys.stderr)
        print("  • Ensure database server is running", file=sys.stderr)
        print("  • Verify credentials and database exists", file=sys.stderr)
        print("  • Check network connectivity and firewall", file=sys.stderr)
        print("📖 See logs for detailed error information.\n", file=sys.stderr)
        raise

def test_database_connection(engine, max_retries=3, retry_delay=2):
    """Test database connection with retry logic for reliability."""
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                # Test basic connectivity
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                
                # Log successful connection
                if attempt > 0:
                    logger.info(f"Database connection established after {attempt + 1} attempts")
                else:
                    logger.info("Database connection established successfully")
                
                return True
                
        except (OperationalError, DisconnectionError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {str(e)}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {str(e)}")
                raise
        
        except SQLAlchemyError as e:
            logger.error(f"Database configuration error: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Unexpected database error: {str(e)}")
            raise

# Create database engine with error handling (skip during testing)
if "pytest" not in sys.modules and settings is not None:
    engine = create_database_engine()
else:
    # For testing, create a placeholder that will be overridden
    engine = None

# Create session factory (skip during testing)
if engine is not None:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # For testing, create a placeholder
    SessionLocal = None

# Create base class for models
Base = declarative_base()

# Dependency to get database session with enhanced error handling
def get_db():
    """Get database session with comprehensive error handling for financial applications."""
    db = SessionLocal()
    try:
        # Test connection health before yielding session
        db.execute(text("SELECT 1"))
        yield db
        
    except (OperationalError, DisconnectionError) as e:
        logger.error(f"Database connection error during session: {str(e)}")
        db.rollback()
        raise
        
    except SQLAlchemyError as e:
        logger.error(f"Database operation error: {str(e)}")
        db.rollback()
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during database session: {str(e)}")
        db.rollback()
        raise
        
    finally:
        try:
            db.close()
        except Exception as e:
            logger.warning(f"Error closing database session: {str(e)}")

def get_db_health():
    """Check database health for monitoring and health checks."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as health_check"))
            result.fetchone()
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
