from pydantic import BaseModel # 데이터관리를 위한 클래스 가져오기

# BaseModel클래스를 상속받아 데이터 관리
# 1개의 클래스로 3개의 데이터를 사용자로부터 입력받는다
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None # 기본값은 None이며 필수 입력값이 아님

# 로그인 요청 데이터
class LoginRequest(BaseModel):
    username: str
    password: str

# 회원가입 요청 데이터
class SignUpRequest(BaseModel):
    username: str
    password: str
    nickname: str

# 글 작성 요청 데이터
class CreateArticleRequest(BaseModel):
    title: str
    content: str