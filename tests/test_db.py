import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base
from main import app, get_session

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

TestingSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def override_get_session():
    async with TestingSessionLocal() as session:
        yield session
        
app.dependency_overrides[get_session] = override_get_session

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
@pytest.mark.asyncio
async def test_create_project():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        
        await ac.post("/register", data={
            "email": "test@example.com",
            "password": "123456"
        })
        
        await ac.post("/login", data={
            "email": "test@example.com",
            "password": "123456"
        })
        
        response = await ac.post(
            "/projects",
            data={"title": "Тестовый проект"},
            follow_redirects=False
        )
        
        assert response.status_code == 303
        assert "/projects/" in response.headers["location"]