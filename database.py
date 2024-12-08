import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

database_name = os.getenv("DATABASE_NAME")
database_username = os.getenv("DATABASE_USERNAME")
database_password = os.getenv("DATABASE_PASSWORD")
database_host = os.getenv("DATABASE_HOST")



database_url: str = f"postgresql://{database_username}:{database_password}@{database_host}/{database_name}"
engine = create_engine(database_url)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    database = sessionLocal()
    try:
        yield database
    finally:
        database.close()


print(f"Database URL: {database_url}")