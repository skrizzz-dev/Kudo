from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None})

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None})

@router.post("/login")
async def login_sumbit(email: str, password: str):
    return {"email": email, "password_len": len(password)}

@router.post("/register")
async def register_sumbit(email: str, password: str):
    return {"email": email, "password_len": len(password)}