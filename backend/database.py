import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Поддержка как SQLite для разработки, так и PostgreSQL для продакшн
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/veres.db",
)

# Настройки для разных типов БД
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
