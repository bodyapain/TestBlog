from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:0080@localhost:5432/blog_db"
engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    photo = Column(Text)
class User(Base):
    __tablename__ = "users"
    user_name = Column(String, primary_key=True, index=True)
    password = Column(String)
    token = Column(String)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
