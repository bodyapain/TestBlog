from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import jwt
from database import SessionLocal, Post, User
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext


app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegistrationRequest(BaseModel):
    user_name: str
    password: str

class LoginRequest(BaseModel):
    user_name: str
    password: str

class PostCreate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    photo: Optional[str]

class PostUpdate(BaseModel):
    title: str
    description: str
    photo: str

class PostResponse(BaseModel):
    user_name: str
    title: Optional[str]
    description: Optional[str]
    photo: Optional[str]

class PostDelete(BaseModel):
    id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/registration",response_model=dict)
def registration(request: RegistrationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_name == request.user_name).first()
    if user:
        raise HTTPException(status_code=401, detail="Такое имя пользователя уже существует")
    hashed_password = pwd_context.hash(request.password)
    user = User(user_name=request.user_name,password=hashed_password)
    # Создаем токен для нового пользователя
    token_data = {"sub": user.user_name}
    token = jwt.encode(token_data, "SECRET_KEY", algorithm="HS256")
    user.token = token
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "access_token": token}


@app.post("/login", response_model=dict)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_name == request.user_name).first()

    if not user:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # Проверяем пароль
    if not pwd_context.verify(request.password, user.password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    token_data = {"sub": user.user_name}
    token = jwt.encode(token_data, "SECRET_KEY", algorithm="HS256")
    user.token = token
    db.commit()
    db.refresh(user)

    # Возвращаем токен вместе с сообщением об успешной авторизации
    return {"message": "Авторизация успешна", "access_token": token}

@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    # Получение всех постов
    posts = db.query(Post).all()
    return posts


@app.post("/posts", response_model=PostResponse)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    authorization: str = Header(None)  # Получаем токен из заголовка
):
    # Раскодируем токен и получим имя пользователя
    try:
        token_data = jwt.decode(authorization, "SECRET_KEY", algorithms=["HS256"])
        user_name = token_data.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Токен недействителен")

    # Получаем токен пользователя из базы данных
    user = db.query(User).filter(User.user_name == user_name).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # Проверяем, совпадает ли токен из запроса с тем, который хранится в базе данных
    if authorization != user.token:
        raise HTTPException(status_code=401, detail="Недостаточно прав для обновления поста")
    # Если пользователь имеет право создавать посты, продолжайте с созданием поста
    db_post = Post(**post.dict())
    db_post.user_name = user_name
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts/{id}", response_model=PostResponse)
def get_post(id: int, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return db_post


@app.put("/posts/{id}", response_model=PostResponse)
def update_post(
        id: int,
        updated_post: PostUpdate,
        db: Session = Depends(get_db),
        authorization: str = Header(None) # Получаем токен из заголовка
):
    try:
        token_data = jwt.decode(authorization, "SECRET_KEY", algorithms=["HS256"])
        user_name = token_data.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Токен недействителен")

    db_post = db.query(Post).filter(Post.id == id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")

    # Получаем токен пользователя из базы данных
    user = db.query(User).filter(User.user_name == user_name).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # Проверяем, совпадает ли токен из запроса с тем, который хранится в базе данных
    if authorization != user.token:
        raise HTTPException(status_code=401, detail="Недостаточно прав для обновления поста")


    for key, value in updated_post.dict().items():
        setattr(db_post, key, value)

    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete("/posts/{id}", response_model=PostDelete)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    authorization: str = Header(None)  # Получаем токен из заголовка
):
    try:
        token_data = jwt.decode(authorization, "SECRET_KEY", algorithms=["HS256"])
        print(token_data)
        user_name = token_data.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истек")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Токен недействителен")

    db_post = db.query(Post).filter(Post.id == id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")

    # Получаем токен пользователя из базы данных
    user = db.query(User).filter(User.user_name == user_name).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # Проверяем, совпадает ли токен из запроса с тем, который хранится в базе данных
    if authorization != user.token:
        raise HTTPException(status_code=401, detail="Недостаточно прав для удаления поста")

    db.delete(db_post)
    db.commit()

    return {"id": id}


