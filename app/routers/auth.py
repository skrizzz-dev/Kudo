from fastapi import APIRouter, Request, HTTPException, status, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_session
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"user": None})

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="register.html", 
        context={"user": None})

@router.post("/login")
async def login_sumbit(
    email: str = Form(...), 
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
    ):
    
    user = await session.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse("/projects", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
    )
    return response
    
@router.post("/register")
async def register_sumbit(
    email: str = Form(...), 
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
    ):
    
    existing = await session.scalar(
        select(User).where(User.email == email)
    )
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Почта уже зарегистрирован",
        )
    
    user = User(
        email=email,
        hashed_password=hash_password(password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse("/projects", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=3600,
    )
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response