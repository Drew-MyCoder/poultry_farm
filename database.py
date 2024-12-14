import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
# from api.auth.model import DBUser

load_dotenv()

database_name = os.getenv("DATABASE_NAME")
database_username = os.getenv("DATABASE_USERNAME")
database_password = os.getenv("DATABASE_PASSWORD")
database_host = os.getenv("DATABASE_HOST")



database_url: str = f"postgresql://{database_username}:{database_password}@{database_host}/{database_name}"
engine = create_engine(database_url)
# Base.metadata.create_all(bind=engine)
sessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()

print('Creating tables....')
Base.metadata.create_all(bind=engine)
print("Tables created successfully")


def get_db():
    database = sessionLocal()
    try:
        yield database
    finally:
        database.close()


print(f"Database URL: {database_url}")


try:
    with engine.connect() as connection:
        print("Connected to the database")
except OperationalError as e:
    print(f"Error connecting to the database {e}" )


# with Session(engine) as session:
#     result = session.query(DBUser)
#     print(result)