from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Sqlite databse file called notes.db will be created automatically
DATABASE_URL = "sqlite:///./notes.db"

# This engine is the connection between python and database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal - Each instance is a database session (Conversation) 
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# All the table models will inherit from this
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()