"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from api.config import settings
from api.db_models import Base

# Database URL
DATABASE_URL = f"mysql+mysqlconnector://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database connection and create tables"""
    try:
        # Test connection
        with engine.connect() as conn:
            print(f"Connected to database: {settings.DB_NAME}")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise


def close_db():
    """Close database connection"""
    engine.dispose()
    print("Database connection closed")


@contextmanager
def get_db_session() -> Session:
    """
    Get database session with context manager
    
    Usage:
        with get_db_session() as db:
            db.query(Student).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """
    Dependency for FastAPI routes
    
    Usage:
        @router.get("/")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
