# import os
# from sqlalchemy import create_engine, inspect, text
# from sqlalchemy.orm import sessionmaker, Session
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.exc import OperationalError
# from dotenv import load_dotenv

# # from api.auth.model import DBUser

# load_dotenv()

# database_name = os.getenv("DATABASE_NAME")
# database_username = os.getenv("DATABASE_USERNAME")
# database_password = os.getenv("DATABASE_PASSWORD")
# database_host = os.getenv("DATABASE_HOST")
# print(f"DATABASE_NAME: {database_name}")
# print(f"DATABASE_USERNAME: {database_username}")
# # print(f"DATABASE_PASSWORD: {database_password}")  # Be careful with this in production!
# print(f"DATABASE_HOST: {database_host}")


# database_url: str = os.getenv("DATABASE_URL")  # Use Render's default DATABASE_URL

# if not database_url:
#     database_url = f"postgresql://{database_username}:{database_password}@{database_host}/{database_name}"
# engine = create_engine(database_url)
# # Base.metadata.create_all(bind=engine)
# sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base = declarative_base()

# print('Creating tables....')
# Base.metadata.create_all(bind=engine)
# print("Tables created successfully")


# def get_db():
#     database = sessionLocal()
#     try:
#         yield database
#     finally:
#         database.close()


# print(f"Database URL: {database_url}")


# try:
#     with engine.connect() as connection:
#         inspector = inspect(engine)
#         tables = inspector.get_table_names()
#         print("Existing table: ", tables)
#         print("Connected to the database")
#         # result = connection.execute(text("SELECT * FROM users LIMIT 1;"))
#         # for row in result:
#         #     print(row)
# except OperationalError as e:
#     print(f"Error connecting to the database {e}" )


# # with Session(engine) as session:
# #     result = session.query(DBUser)
# #     print(result)


import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Import ALL your models here to ensure they're loaded
from api.auth.model import (
    DBUser, 
    DBBlacklistedToken, 
    DBReset, 
    DBCoops, 
    DBBuyer, 
    DBExpenditure
)

load_dotenv()

# Database connection setup (unchanged)
database_name = os.getenv("DATABASE_NAME")
database_username = os.getenv("DATABASE_USERNAME")
database_password = os.getenv("DATABASE_PASSWORD")
database_host = os.getenv("DATABASE_HOST")

database_url: str = os.getenv("DATABASE_URL")  # Use Render's default DATABASE_URL

if not database_url:
    database_url = f"postgresql://{database_username}:{database_password}@{database_host}/{database_name}"

# Create engine with additional parameters for better connection handling
engine = create_engine(
    database_url, 
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

Base = declarative_base()

# Debugging: Print out all tables that will be created
print("Tables to be created:")
for table_name in Base.metadata.tables:
    print(f"- {table_name}")

try:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")

    # Verify table creation
    with engine.connect() as connection:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("Existing tables:", tables)
except Exception as e:
    print(f"Error creating tables: {e}")
    import traceback
    traceback.print_exc()

# Session configuration
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    database = sessionLocal()
    try:
        yield database
    finally:
        database.close()

print(f"Database URL: {database_url}")