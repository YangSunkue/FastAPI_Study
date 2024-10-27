from sqlalchemy import *
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from dotenv import load_dotenv
import os
from typing import AsyncGenerator

# 환경변수 로드
load_dotenv()
DB_URL = os.getenv("DB_URL")

Base: DeclarativeMeta = declarative_base()

class AsyncDatabaseSession:

    def __init__(self):
        # 비동기 DB 엔진 생성
        self.engine = create_async_engine(
            DB_URL,
            pool_recycle=500, # 커넥션을 500초마다 재생성
            echo=True # SQL 쿼리 로깅 활성화
        )
        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    # 모든 모델의 테이블 생성
    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    # 모든 테이블 삭제
    async def drop_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    # 데이터베이스 세션 생성 및 관리
    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

db = AsyncDatabaseSession()

# FastAPI 의존성 주입을 위한 함수
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db.get_db():
        yield session

    

# class EngineConn:

#     # 생성자, EngineConn 인스턴스가 생성될 때 초기값을 할당한다 ( DB 엔진 초기화 )
#     def __init__(self):
#         self.engine = create_async_engine(DB_URL, pool_recycle = 500) # 500초마다 재연결
#         self.MyAsyncSession = sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False) # 비동기 세션 클래스 반환(아직 인스턴스 아님)

#     # ORM 방식 비동기 세션 생성
#     async def create_session(self):
#         async with self.MyAsyncSession() as session: # MyAsyncSession으로 생성된 세션을 session에 할당함
#             yield session
#             # yield + Depends 합쳐서 사용할 경우에만 자동 세션 정리
#             # Depends를 사용하지 않으면 명시적으로 close해야 함
    
#     # 기본 방식
#     async def connection(self):
#         conn = await self.engine.connect()
#         return conn