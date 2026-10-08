from fastapi import FastAPI, Request, HTTPException, Depends

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form
from app.models.board import Board

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_optional_user
from app.database import get_session
from app.models.user import User
from app.models.project import Project
from app.routers import auth, users
from app.constants import BOARD_COLORS

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

@app.post("/projects")
async def project_create(
    title: str = Form(...),
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse("/login", status_code=303)
    
    project = Project(user_id=user.id, title=title)
    session.add(project)
    await session.flush()
    
    default_boards = ["To Do", "In Progress", "Done"]
    for i, board_title in enumerate(default_boards):
        session.add(Board(
            project_id=project.id,
            title=board_title,
            position=i,
        ))
    await session.commit()
    
    return RedirectResponse(f"/projects/{project.id}", status_code=303)

@app.post("/boards/{board_id}/color")
async def set_board_color(
    board_id: int,
    color: str = Form(...),
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    if color not in BOARD_COLORS:
        raise HTTPException(400, "Неверный цвет")

    board = await session.get(Board, board_id)
    if not board:
        raise HTTPException(404, "Доска не найдена")
    
    project = await session.get(Project, board.project_id)
    if project.user_id != user.id:
        raise HTTPException(403, "Нет доступа")
    
    board.color = color
    await session.commit()
    
    return RedirectResponse(f"/projects/{board.project_id}", status_code=303)

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def board_view(
    request: Request, 
    project_id: int, 
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse("/login", status_code=303)
    
    project = await session.scalar(
        select(Project)
        .where(Project.id == project_id, Project.user_id == user.id)
        .options(selectinload(Project.boards).selectinload(Board.cards))
    )
    
    if not project:
        raise HTTPException(404, "Проект не найден")
        
    return templates.TemplateResponse(
        request=request, 
        name="board.html", 
        context={
            "user": user, 
            "project": project, 
            "columns": project.boards,
            "BOARD_COLORS": BOARD_COLORS,
            },
        )