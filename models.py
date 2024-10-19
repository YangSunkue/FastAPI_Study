from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# db.py에서 연결한 db를 MySQL 테이블과 매핑시킨다
class Users(Base):
    __tablename__ = "users" # 테이블명
    
    id = Column(String(100), primary_key=True, nullable=False) # id 필드
    pw = Column(String(2000), nullable=False) # pw 필드
    nickname = Column(String(20), unique=True, nullable=False) #nickname 필드

