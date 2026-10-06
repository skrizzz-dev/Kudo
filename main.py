from fastapi import FastAPI, Request, Depends

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.models.board import Board

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_user
from app.database import get_session
from app.models.user import User
from app.models.project import Project
from app.routers import auth, users

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User | None = Depends(get_optional_user)):
    if user:
        return RedirectResponse("/projects", status_code=303)
    return templates.TemplateResponse(request=request, name="landing.html", context={"user": user})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, user: User | None = Depends(get_optional_user)):
    return templates.TemplateResponse(request=request, name="about.html", context={"user": user})

@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request, user: User | None = Depends(get_optional_user), session: AsyncSession = Depends(get_session)):
    if not user:
        return RedirectResponse("/login", status_code=303)
    
    result = await session.scalars(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
    )
    projects = result.all()
    
    return templates.TemplateResponse(request=request, name="projects.html", context={"user": user, "projects": projects})

@app.get("/projects/new", response_class=HTMLResponse)
async def project_new_form(
    request: Request,
    user: User | None = Depends(get_optional_user)
):
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="project_new.html", context={"user": user})

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def board_view(request: Request, project_id: int, user: User | None = Depends(get_optional_user)):
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request=request, name="board.html", context={"user": None, "project": FAKE_BOARD["project"], "columns": FAKE_BOARD["columns"]})