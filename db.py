from sqlalchemy import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
DB_URL = os.getenv("DB_URL")

class EngineConn:

    # 생성자, EngineConn 인스턴스가 생성될 때 초기값을 할당한다 ( DB 엔진 초기화 )
    def __init__(self):
        self.engine = create_async_engine(DB_URL, pool_recycle = 500) # 500초마다 재연결
        self.MyAsyncSession = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False) # 비동기 세션 클래스 반환(아직 인스턴스 아님)

    # ORM 방식 비동기 세션 생성
    async def create_session(self):
        async with self.MyAsyncSession() as session: # MyAsyncSession으로 생성된 세션을 session에 할당함
            yield session
            # yield + Depends 합쳐서 사용할 경우에만 자동 세션 정리
            # Depends를 사용하지 않으면 명시적으로 close해야 함
    
    # 기본 방식
    async def connection(self):
        conn = await self.engine.connect()
        return conn