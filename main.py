# 기본 import
from typing import Union # 여러개의 데이터타입 허용
from fastapi import FastAPI, Depends, HTTPException # FastAPI, 의존성주입, HTTP오류처리 가져오기
from fastapi.responses import JSONResponse # JSON 응답
from datetime import datetime, timedelta, timezone # 시간 관련 모듈
from dotenv import load_dotenv # 환경변수 모듈
import os # 환경변수 가져오기 위한 클래스
import hashlib # 해시함수
import jwt # JWT

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession # 비동기 SQLAlchemy 세션 사용을 위한 클래스 가져오기
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select # 비동기 select 쿼리
from sqlalchemy import insert # 비동기 insert 쿼리

# 파일 import
from db import EngineConn # db연결 클래스 가져오기
from models import Users # db 매핑 테이블 가져오기
from schemas import Item, LoginRequest, SignUpRequest # 데이터 스키마 가져오기

#####################################################################################

# POST : 데이터 생성 및 전달 (create)
# GET : 데이터 조회 (read)
# PUT : 데이터 업데이트 (update)
# DELETE : 데이터 삭제 (delete)
# 인자 인식 순서 : 경로, 파라미터, body, Depends

app = FastAPI() # FastAPI 사용
engine = EngineConn() # DB 인스턴스 생성 및 생성자를 통한 DB엔진 초기화

# .env 파일 환경변수 로드
load_dotenv()
SecretKey = os.getenv("SecretKey")
Algorithm = os.getenv("Algorithm")
AccessTokenExpireMinutes = int(os.getenv("AccessTokenExpireMinutes", 60))

# 로그인
@app.post("/login")
async def login(loginData: LoginRequest,
    db: AsyncSession = Depends(engine.createSession)):

    try:
        # 유저정보 조회
        query = select(Users).where(Users.id == loginData.userName)
        re = await db.execute(query)
        result = re.scalars().first()

        # 존재하지 않는 유저
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 패스워드 불일치
        hashedPassword = hashlib.sha256(loginData.password.encode()).hexdigest() # 패스워드 해시
        if hashedPassword != result.pw:
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # JWT Access Token 발급
        expiration = datetime.now(timezone.utc) + timedelta(minutes=AccessTokenExpireMinutes)
        tokenData = {
            "sub" : loginData.userName,
            "exp" : expiration
        }
        accessToken = jwt.encode(tokenData, SecretKey, algorithm=Algorithm)
        
        # 로그인 성공
        return JSONResponse(content={
            "message" : "Logged in successfully",
            "userId" : loginData.userName,
            "accessToken" : accessToken
            },
            status_code=200)

    except Exception as error:
        # HTTPException일 경우 그대로 반환
        if isinstance(error, HTTPException):
            raise error
        
        # 이외 모든 오류는 500 반환
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 회원가입
@app.post("/signUp")
async def signUp(signUpData: SignUpRequest,
    db: AsyncSession = Depends(engine.createSession)):
    
    try:
        # 아이디 중복검사
        existingUser = await db.execute(select(Users.id).where(Users.id == signUpData.userName))
        if existingUser.scalar_one_or_none(): # 결과가 1개만 있으면 해당 결과 반환, 없으면 None, 2개이상이면 예외
            raise HTTPException(status_code=409, detail="Username already exists")
        
        # 닉네임 중복검사
        existingNickName = await db.execute(select(Users.nickname).where(Users.nickname == signUpData.nickName))
        if existingNickName.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Nickname already exists")
        

        # 회원가입 진행
        hashedPassword = hashlib.sha256(signUpData.password.encode()).hexdigest() # 패스워드 해시

        # Users 인스턴스 생성
        newUser = Users(
            id=signUpData.userName,
            pw=hashedPassword,
            nickname=signUpData.nickName
        )

        # db에 insert 및 커밋
        db.add(newUser)
        await db.commit()

        return JSONResponse(content={"message" : "Sign up successful", "userId" : signUpData.userName}, status_code=201)

    # IntegrityError : 무결성 제약조건 위반 에러
    except IntegrityError as integrityError:
        await db.rollback()
        print(f"Database integrity error: {integrityError}")
        raise HTTPException(status_code=400, detail="Sign up failed due to a conflict")
    
    except Exception as error:
        await db.rollback()
        if isinstance(error, HTTPException):
            raise error
        
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error")




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