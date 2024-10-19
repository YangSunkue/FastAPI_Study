from typing import Union
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# 파일 import
from db import EngineConn
from models import Users

app = FastAPI()

# DB 연결
engine = EngineConn()
# MyAsyncSession = engine.createSession

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None


# 이렇게 매번 Depends 해서 인자 부분 길게 가져가는거 개선법 있나 찾아보자
# 다른 사람 코드 참고해봐야 할듯
@app.get("/test")
async def test(db: AsyncSession = Depends(engine.createSession)):
    result = await db.execute(select(Users))
    example = result.scalars().all()
    print(example)
    return example

@app.get("/")
async def read_root():
    return {"Hello" : "World"}

# FastAPI는 입력된 값을 지정된 자료형으로 변환된다.
@app.get("/items/{item_id}")
async def read_item(item_id : int, q : Union[str, None] = None):
    return {"item_id" : item_id, "q" : q}

# update하므로 put
@app.put("/items/{item_id}")
async def update_item(item_id : int, item : Item):
    return {"item_price" : item.price, "item_id" : item_id}