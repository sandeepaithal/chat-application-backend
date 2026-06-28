from sqlalchemy import create_engine
# Creates database sessions
from sqlalchemy.orm import sessionmaker
# Base class for all database models
from sqlalchemy.orm import declarative_base
# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

# Replace YOUR_PASSWORD with your MySQL password
# Format:
# mysql+pymysql://username:password@host/database_name

DATABASE_URL = (
    "mysql+pymysql://root:admin@localhost/chat_app"
)

# --------------------------------------------------
# DATABASE ENGINE
# --------------------------------------------------

# echo=True prints SQL queries in terminal
# Useful while learning/debugging

engine = create_engine(
    DATABASE_URL,
    echo=True
)

# --------------------------------------------------
# SESSION FACTORY
# --------------------------------------------------

# Every database operation will use a session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# --------------------------------------------------
# BASE CLASS
# --------------------------------------------------

# All models inherit from Base

Base = declarative_base()


# --------------------------------------------------
# DATABASE DEPENDENCY
# --------------------------------------------------

# FastAPI will use this function
# to open and close database sessions safely

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()