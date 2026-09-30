from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import auth, users

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(users.router)

FAKE_PROJECTS = [
    {"id": 1, "title": "Работа", "boards_count": 3},
    {"id": 2, "title": "Учёба", "boards_count": 5},
    {"id": 3, "title": "Личное", "boards_count": 3},
]

FAKE_BOARD = {
    "project": {"id": 1, "title": "Работа"},
    "columns": [
        {
            "id": 1,
            "title": "To Do",
            "cards": [
                {"id": 1, "title": "Написать отчёт", "description": "До пятницы"},
                {"id": 2, "title": "Позвонить клиенту", "description": ""},
            ],
        },
        {
            "id": 2,
            "title": "In Progress",
            "cards": [
                {"id": 3, "title": "Обновить сайт", "description": "Главная страница"},
            ],
        },
        {
            "id": 3,
            "title": "Done",
            "cards": [
                {"id": 4, "title": "Совещание", "description": "Обсудили план"},
            ],
        },
    ],
}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html", context={})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="about.html", context={})

@app.get("/projects", response_class=HTMLResponse)
async def projects_list(request: Request):
    return templates.TemplateResponse(request=request, name="projects.html", context={"user": None, "projects": FAKE_PROJECTS})

@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def board_view(request: Request, project_id: int):
    return templates.TemplateResponse(request=request, name="board.html", context={"user": None, "project": FAKE_BOARD["project"], "columns": FAKE_BOARD["columns"]})