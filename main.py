from typing import Union # 여러개의 데이터타입 허용
from fastapi import FastAPI, Depends, HTTPException # FastAPI, 의존성주입, HTTP오류처리 가져오기
from fastapi.responses import JSONResponse # JSON 응답
from pydantic import BaseModel # 데이터관리를 위한 클래스 가져오기
from sqlalchemy.ext.asyncio import AsyncSession # 비동기 SQLAlchemy 세션 사용을 위한 클래스 가져오기
from sqlalchemy.future import select # 비동기 select 쿼리

# 파일 import
from db import EngineConn # db연결 클래스 가져오기
from models import Users # models.py에서 매핑된 테이블 가져오기

app = FastAPI()

# DB 인스턴스 생성 및 생성자를 통한 DB엔진 초기화
engine = EngineConn()

# BaseModel클래스를 상속받아 데이터 관리
# 1개의 클래스로 3개의 데이터를 사용자로부터 입력받는다
class Item(BaseModel):
    name: str
    price: float
    isOffer: bool = None # 기본값은 None이며 필수 입력값이 아님


@app.get("/test")
async def test(db: AsyncSession = Depends(engine.createSession)):
    try:
        result = await db.execute(select(Users))
        re = result.scalars().all()
        userData = [{"id" : user.id, "pw" : user.pw, "nickname" : user.nickname} for user in re]
        return JSONResponse(content={"userData" : userData}, status_code=200) 
    
    except Exception as error:
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error") # 에러 상황의 응답



@app.get("/")
async def readRoot():
    return {"Hello" : "World"}

# FastAPI는 입력된 값을 지정된 자료형으로 변환된다.
@app.get("/items/{itemId}")
async def readItem(itemId : int, q : Union[str, None] = None):
    return {"itemId" : itemId, "q" : q}

# update하므로 put
@app.put("/items/{itemId}")
async def updateItem(itemId : int, item : Item):
    return {"itemPrice" : item.price, "itemId" : itemId}