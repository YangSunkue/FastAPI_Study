from sqlalchemy import Column, String, Integer, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# db.py에서 연결한 db를 MySQL 테이블과 매핑시킨다
class Users(Base):
    __tablename__ = "users" # 테이블명
    
    id = Column(String(100), primary_key=True, nullable=False) # id 필드
    pw = Column(String(2000), nullable=False) # pw 필드
    nickname = Column(String(20), unique=True, nullable=False) #nickname 필드

    def __repr__(self):
        return f"<Users(id={self.id}, pw={self.pw}, nickname={self.nickname})>"

class Articles(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    author_nickname = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=True)
    author_id = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title}, author_nickname={self.author_nickname}, created_at={self.created_at}, author_id={self.author_id})>"