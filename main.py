# 기본 import
from typing import Union, Dict # 여러개의 데이터타입 허용
from fastapi import FastAPI, Depends, HTTPException # FastAPI, 의존성주입, HTTP오류처리 가져오기
from fastapi.responses import JSONResponse # JSON 응답
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer # JWT 인증을 위한 클래스
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
from models import Users, Articles # db 매핑 테이블 가져오기
from schemas import Item, LoginRequest, SignUpRequest, CreateArticleRequest # 데이터 스키마 가져오기

#####################################################################################

# POST : 데이터 생성 및 전달 (create)
# GET : 데이터 조회 (read)
# PUT : 데이터 업데이트 (update)
# DELETE : 데이터 삭제 (delete)
# 인자 인식 순서 : 경로, 파라미터, body, Depends

app = FastAPI() # FastAPI 사용
engine = EngineConn() # DB 인스턴스 생성 및 생성자를 통한 DB엔진 초기화
security = HTTPBearer() # JWT Access Token을 Bearer토큰 자동 인식하여 가져오기, HTTPAuthorizationCredentials 인스턴스 형태이다.

# .env 파일 환경변수 로드
load_dotenv()
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


# 토큰 검증 + 사용자 정보 리턴
async def verify_token_and_get_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials # 토큰 문자열 형태로 꺼내기
    try:
        # 토큰 검증
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username: str = payload.get("sub")
        nickname: str = payload.get("nickname")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # 사용자 정보 리턴
        return {"username" : username, "nickname" : nickname}
    
    # 토큰 만료
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    
    # 유효하지 않은 토큰
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


#####################################################################################

# 회원가입
@app.post("/api/sign_up")
async def sign_up(sign_up_data: SignUpRequest,
    db: AsyncSession = Depends(engine.create_session)):
    
    try:
        # 아이디 중복검사
        existing_user = await db.execute(select(Users.id).where(Users.id == sign_up_data.username))
        if existing_user.scalar_one_or_none(): # 결과가 1개만 있으면 해당 결과 반환, 없으면 None, 2개이상이면 예외
            raise HTTPException(status_code=409, detail="_n already exists")
        
        # 닉네임 중복검사
        existing_nickname = await db.execute(select(Users.nickname).where(Users.nickname == sign_up_data.nickname))
        if existing_nickname.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Nickname already exists")
        

        # 회원가입 진행
        hashed_password = hashlib.sha256(sign_up_data.password.encode()).hexdigest() # 패스워드 해시

        # Users 인스턴스 생성
        new_user = Users(
            id=sign_up_data.username,
            pw=hashed_password,
            nickname=sign_up_data.nickname
        )

        # db에 insert 및 커밋
        db.add(new_user)
        await db.commit()

        return JSONResponse(content={"message" : "Sign up successful", "user_id" : sign_up_data.username}, status_code=201)

    # IntegrityError : 무결성 제약조건 위반 에러
    except IntegrityError as integrity_error:
        await db.rollback()
        print(f"Database integrity error: {integrity_error}")
        raise HTTPException(status_code=400, detail="Sign up failed due to a conflict")
    
    except Exception as error:
        await db.rollback()
        if isinstance(error, HTTPException):
            raise error
        
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 로그인
@app.post("/api/login")
async def login(login_data: LoginRequest,
    db: AsyncSession = Depends(engine.create_session)):

    try:
        # 유저정보 조회
        query = select(Users).where(Users.id == login_data.username)
        re = await db.execute(query)
        result = re.scalars().first()

        # 존재하지 않는 유저
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 패스워드 불일치
        hashed_password = hashlib.sha256(login_data.password.encode()).hexdigest() # 패스워드 해시
        if hashed_password != result.pw:
            raise HTTPException(status_code=401, detail="Incorrect password")
        
        # JWT Access Token 발급
        expiration = datetime.now(timezone.utc) + timedelta(minutes=access_token_expire_minutes)
        token_data = {
            "sub" : login_data.username,
            "nickname" : result.nickname,
            "exp" : expiration
        }
        access_token = jwt.encode(token_data, secret_key, algorithm=algorithm)
        
        # 로그인 성공
        return JSONResponse(content={
            "message" : "Logged in successfully",
            "user_id" : login_data.username,
            "nickname" : result.nickname,
            "access_token" : access_token
            },
            status_code=200)

    except Exception as error:
        # HTTPException일 경우 그대로 반환
        if isinstance(error, HTTPException):
            raise error
        
        # 이외 모든 오류는 500 반환
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 글쓰기
@app.post("/api/articles")
async def create_article(create_article_data: CreateArticleRequest,
    current_user: Dict[str, str] = Depends(verify_token_and_get_user),
    db: AsyncSession = Depends(engine.create_session)):

    try:
        # 작성시간 계산 (한국 표준시)
        kst = timezone(timedelta(hours=9))
        created_at = datetime.now(kst)

        # 새 글 인스턴스 생성
        new_article = Articles(
            title = create_article_data.title,
            content = create_article_data.content,
            author_nickname = current_user.get("nickname"),
            created_at = created_at,
            author_id = current_user.get("username")
        )

        # DB에 insert
        db.add(new_article)
        await db.commit()
        await db.refresh(new_article)

        # 글쓰기 성공
        if new_article.id:
            return JSONResponse(content={"message" : "Article created successfully", "article_id" : new_article.id})
        # 글쓰기 실패
        else:
            raise HTTPException(status_code=500, detail="Article creation failed")

    
    except Exception as error:
        await db.rollback()
        if isinstance(error, HTTPException):
            raise error

        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





@app.get("/test")
async def test(db: AsyncSession = Depends(engine.create_session)):

    try:
        query = select(Users)
        re = await db.execute(query)
        result = re.scalars().all()
        user_data = [{"id" : user.id, "pw" : user.pw, "nickname" : user.nickname} for user in result]

        return JSONResponse(content={"user_data" : user_data}, status_code=200) # 일반적인 응답
    
    except Exception as error:
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=500, detail="Internal Server Error") # 에러 상황의 응답

@app.get("/")
async def read_root():
    return {"Hello" : "World"}

# FastAPI는 입력된 값을 지정된 자료형으로 변환된다.
@app.get("/items/{itemId}")
async def read_item(item_id : int, q : Union[str, None] = None):
    return {"item_id" : item_id, "q" : q}

# update하므로 put
@app.put("/items/{itemId}")
async def update_item(item_id : int, item : Item):
    return {"item_price" : item.price, "item_id" : item_id}