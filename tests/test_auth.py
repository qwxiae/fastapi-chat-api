import pytest 
from conftest import _register_and_login



@pytest.mark.asyncio
async def test_register_success(client):
    response = await client.post(
        "/auth/register", 
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    # never leak the hash
    assert "password" not in data  

@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {
        "username": "user1",
        "email": "dupe@example.com",
        "password": "password123",
    }
    await client.post("/auth/register", json=payload)

    payload["username"] = "user2"
    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={
            "username": "user1",
            "email": "dupe@example.com",
            "password": "password123",
        }
    )
    response = await client.post(
        "/auth/login",
        json={
            "email": "dupe@example.com",
            "password": "password123",
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={
            "username": "user1",
            "email": "dupe@example.com",
            "password": "password123",
        }
    )
    response = await client.post(
        "/auth/login",
        json={
            "email": "dupe@example.com",
            "password": "wrongpassword123",
        }
    )
    assert response.status_code == 401
    assert "password" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    response = await client.post("/auth/logout")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_with_token(client):
    await client.post(
        "/auth/register",
        json={
            "username": "user1",
            "email": "dupe@example.com",
            "password": "password123",
        }
    )
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "dupe@example.com",
            "password": "password123",
        }
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = await client.post(
        "/auth/logout",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_upload_avatar(client):
    headers = await _register_and_login(client, "avataruser", "avatar@example.com")

    # tiny valid 1x1 PNG, generated as raw bytes — no need for a real file on disk
    png_bytes = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    response = await client.post(
        "/users/me/avatar",
        files={"file": ("avatar.png", png_bytes, "image/png")},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["avatar_url"].startswith("/uploads/avatars/")


@pytest.mark.asyncio
async def test_upload_avatar_wrong_type(client):
    headers = await _register_and_login(client, "baduser", "bad@example.com")

    response = await client.post(
        "/users/me/avatar",
        files={"file": ("evil.exe", b"not an image", "application/x-msdownload")},
        headers=headers,
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_avatar_too_large(client, monkeypatch):
    headers = await _register_and_login(client, "biguser", "big@example.com")

    from app.core import config
    # force any file to exceed limit
    monkeypatch.setattr(config.settings, "max_upload_size_mb", 0)  

    response = await client.post(
        "/users/me/avatar",
        files={"file": ("avatar.png", b"x" * 1024, "image/png")},
        headers=headers,
    )

    assert response.status_code == 413