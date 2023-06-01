from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


def get_session():
    load_dotenv()
    engine = create_engine(os.getenv('path_to_database'))
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
