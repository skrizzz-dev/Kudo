import pytest
from httpx import AsyncClient, ASGITransport
from main import app

# проверка get запроса главной страницы
@pytest.mark.asyncio
async def test_get_main():
    async with AsyncClient(transport=ASGITransport(app=app), 
                           base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert "Kudo" in response.text  

# проверка работы редиректа на логин при get запросе /projects
@pytest.mark.asyncio
async def test_projects_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), 
                            base_url="http://test") as ac:
        response = await ac.get("/projects", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"