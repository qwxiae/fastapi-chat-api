import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

# swap dependency `get_db` in endpoints for testing 
app.dependency_overrides[get_db] = override_get_db


async def _register_and_login(
    client,
    username="roomowner",
    email="owner@example.com",
):
    await client.post("/auth/register", json={
    "username": username,
    "email": email,
    "password": "password123",
})
    login_response = await client.post("/auth/login", json={
        "email": email,
        "password": "password123",
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ================ Global Fixtures ==================
@pytest.fixture(autouse=True, scope="session")
def init_cache():
    """fastapi-cache needs to be initialised once, since lifespan never runs in tests."""
    FastAPICache.init(InMemoryBackend(), prefix="test-cache")

# runs automatically before every single test
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# ================ Fixtures ==================

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
