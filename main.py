from typing import Union # 여러개의 데이터타입 허용
from fastapi import FastAPI, Depends, HTTPException # FastAPI, 의존성주입, HTTP오류처리 가져오기
from fastapi.responses import JSONResponse # JSON 응답
from pydantic import BaseModel # 데이터관리를 위한 클래스 가져오기
from sqlalchemy.ext.asyncio import AsyncSession # 비동기 SQLAlchemy 세션 사용을 위한 클래스 가져오기
from sqlalchemy.future import select # 비동기 select 쿼리

# 파일 import
from db import EngineConn # db연결 클래스 가져오기
from models import Users # db 매핑 테이블 가져오기
from schemas import Item, LoginRequest # 데이터 스키마 가져오기

app = FastAPI()

# DB 인스턴스 생성 및 생성자를 통한 DB엔진 초기화
engine = EngineConn()

# POST : 데이터 생성 및 전달 (create)
# GET : 데이터 조회 (read)
# PUT : 데이터 업데이트 (update)
# DELETE : 데이터 삭제 (delete)
# 인자 인식 순서 : 경로, 파라미터, body, Depends

@app.get("/test")
async def test(db: AsyncSession = Depends(engine.createSession)):
    try:
        query = select(Users)
        re = await db.execute(query)
        result = re.scalars().all()
        userData = [{"id" : user.id, "pw" : user.pw, "nickname" : user.nickname} for user in result]

        return JSONResponse(content={"userData" : userData}, status_code=200) # 일반적인 응답
    
    except Exception as error:
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error") # 에러 상황의 응답

# 로그인
# 비밀번호 해시 추가해야 함
@app.post("/login")
async def login(loginData: LoginRequest,
    db: AsyncSession = Depends(engine.createSession)):

    try:
        # 유저정보 조회
        query = select(Users).where(Users.id == loginData.username)
        re = await db.execute(query)
        result = re.scalars().first()

        # 존재하지 않는 유저
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 패스워드 불일치
        if loginData.password != result.pw:
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # JWT Access Token 발급
        
        # 로그인 성공
        return JSONResponse(content={"message" : "Logged in successfully", "userId" : loginData.username}, status_code=200)

    except Exception as error:
        # HTTPException일 경우 그대로 반환
        if isinstance(error, HTTPException):
            raise error
        
        # 이외 모든 오류는 500 반환
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





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