from sqlalchemy import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DB_URL = "mysql+aiomysql://root:0000@localhost:3306/practice"

class EngineConn:

    # 생성자, EngineConn 인스턴스가 생성될 때 초기값을 할당한다 ( DB 엔진 초기화 )
    def __init__(self):
        self.engine = create_async_engine(DB_URL, pool_recycle = 500)
        self.MyAsyncSession = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False) # 비동기 세션 클래스 반환(아직 인스턴스 아님)

    # ORM 방식 비동기 세션 생성
    async def createSession(self):
        async with self.MyAsyncSession() as session:
            yield session
    
    # 기본 방식
    async def connection(self):
        conn = await self.engine.connect()
        return conn