from fastapi import FastAPI, Request, HTTPException, Depends

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_optional_user
from app.database import get_session
from app.models.user import User
from app.models.project import Project
from app.models.card import Card
from app.models.board import Board
from app.routers import auth, users
from app.constants import BOARD_COLORS
from app.schemas.card import CardMove

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

@app.post("/boards")
async def board_create(
    title: str = Form(...),
    project_id: int = Form(...),
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
):
    if not user:
        raise HTTPException(401, "Не автризован")

    project = await session.get(Project, project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(403, "Нет доступа")
    
    boards_count = await session.scalar(
        select(func.count()).select_from(Board).where(Board.project_id == project_id))
    if boards_count >= 9:
        raise HTTPException(400, "Всего колонок не должно быть больше 9")
    
    max_position = await session.scalar(
        select(func.max(Board.position)).where(Board.project_id == project_id)
    )
    position = (max_position or 0) + 1
    
    board = Board(
        project_id=project_id,
        title=title,
        position=position,
    )
    session.add(board)
    await session.commit()
    
    return RedirectResponse(f"/projects/{project_id}", status_code=303)
    
@app.post("/boards/{board_id}/rename")
async def board_rename(
    board_id: int,
    title: str = Form(...),
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return HTTPException(401, "Не авторизован")
    
    board = await session.get(Board, board_id)
    if not board:
        raise HTTPException(404, "Доска не найдена")
    
    project = await session.get(Project, board.project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(403, "Нет доступа")
    
    board.title = title.strip()
    await session.commit()
    
    return RedirectResponse(f"/projects/{project.id}", status_code=303)

@app.post("/cards")
async def card_create(
    title: str = Form(...),
    description: str = Form(""),
    board_id: int = Form(...),
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse("/login", status_code=303)

    board = await session.get(Board, board_id)
    if not board:
        raise HTTPException(404, "Не удалось найти доску")
    
    project = await session.get(Project, board.project_id)
    if project.user_id != user.id:
        raise HTTPException(403, "Нет доступа к проекту")
    
    max_position = await session.scalar(select(func.max(Card.position)).where(Card.board_id == board_id))
    position = (max_position or 0) + 1
    
    card = Card(
        board_id=board_id,
        title=title,
        description=description or None,
        position=position,
    )
    
    session.add(card)
    await session.commit()
    
    return RedirectResponse(f"/projects/{project.id}", status_code=303)

@app.post("/cards/{card_id}/delete")
async def card_delete(
    card_id: int,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
):
    if not user:
        return RedirectResponse("/login")
    
    card = await session.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Карточка не найдена")
    
    board = await session.get(Board, card.board_id)
    project = await session.get(Project, board.project_id)
    if project.user_id != user.id:
        raise HTTPException(403, "Нет доступа к проекту")
    
    await session.delete(card)
    await session.commit()
    
    return RedirectResponse(f"/projects/{project.id}", status_code=303)

@app.patch("/cards/{card_id}/move")
async def move_card(
    card_id: int,
    data: CardMove,
    user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(401, "Не авторизован")
   
    card = await session.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Карточка не найдена")
    
    board = await session.get(Board, card.board_id)
    project = await session.get(Project, board.project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(403, "Нет доступа к проекту")
    
    new_board = await session.get(Board, data.board_id)
    if not new_board or new_board.project_id != project.id:
        raise HTTPException(400, "Неверная доска")
    
    old_board_id = card.board_id
    
    if old_board_id != data.board_id:
        card.board_id = data.board_id
        cards = (await session.scalars(
            select(Card).where(Card.board_id == old_board_id).order_by(Card.position)
        )).all()
        
        for i, c in enumerate(cards):
            c.position = i
            
    cards = (await session.scalars(
        select(Card)
        .where(Card.board_id == data.board_id, Card.id != card.id)
        .order_by(Card.position)
    )).all()
    
    # Проверка границ позиций
    pos = max(0, min(data.position, len(cards)))
    cards.insert(pos, card)
    
    for i, c in enumerate(cards):
        c.position = i
        
    await session.commit()
