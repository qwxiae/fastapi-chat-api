import pytest
from conftest import _register_and_login


@pytest.mark.asyncio
async def test_create_room(client):
    auth_header = await _register_and_login(client)

    room_name = "test_room"

    response = await client.post(
        "/rooms",
        json={
            "name": room_name,
            "description": "General chat",
            "is_private": False,
        },
        headers=auth_header,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == room_name
    assert data["is_private"] is False


@pytest.mark.asyncio
async def test_create_room_duplicate_name_same_owner(client):
    auth_header = await _register_and_login(client)
    payload = {"name": "general", "description": "First", "is_private": False}
    await client.post("/rooms", json=payload, headers=auth_header)

    response = await client.post("/rooms", json=payload, headers=auth_header)
    assert response.status_code in (400, 409, 500)


@pytest.mark.asyncio
async def test_creator_is_automatically_admin(client):
    auth_header = await _register_and_login(client)

    create_response = await client.post(
        "/rooms",
        json={
            "name": "adminroom",
            "is_private": False,
        },
        headers=auth_header,
    )
    room_id = create_response.json()["id"]

    members_response = await client.get(
        f"/rooms/{room_id}/members", headers=auth_header
    )
    members = members_response.json()

    assert len(members) == 1
    assert members[0]["role"] == "admin"


@pytest.mark.asyncio
async def test_join_public_room(client):
    auth_header = await _register_and_login(client)
    create_response = await client.post(
        "/rooms",
        json={
            "name": "adminroom",
            "is_private": False,
        },
        headers=auth_header,
    )

    room_id = create_response.json()["id"]

    auth_header_user2 = await _register_and_login(
        client,
        username="user2",
        email="user2@example.com",
    )
    response = await client.post(f"/rooms/{room_id}/join", headers=auth_header_user2)
    assert response.status_code == 200
    data = response.json()
    assert data["room_id"] == room_id
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_cannot_join_private_room(client):
    auth_header_owner = await _register_and_login(client)
    create_response = await client.post(
        "/rooms",
        json={
            "name": "adminroom",
            "is_private": True,
        },
        headers=auth_header_owner,
    )

    room_id = create_response.json()["id"]

    auth_header_user2 = await _register_and_login(
        client,
        username="user2",
        email="user2@example.com",
    )
    response = await client.post(f"/rooms/{room_id}/join", headers=auth_header_user2)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_member_cannot_send_message(client):
    auth_header_owner = await _register_and_login(client)
    create_response = await client.post(
        "/rooms",
        json={
            "name": "adminroom",
            "is_private": True,
        },
        headers=auth_header_owner,
    )

    room_id = create_response.json()["id"]

    auth_header_user2 = await _register_and_login(
        client,
        username="user2",
        email="user2@example.com",
    )

    message = "Hello world!"
    response = await client.post(
        f"/rooms/{room_id}/messages",
        headers=auth_header_user2,
        json={"content": message},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_member_can_send_and_list_messages(client):
    # Owner creates room
    auth_header = await _register_and_login(client)
    room_response = await client.post(
        "/rooms",
        json={
            "name": "adminroom",
            "is_private": False,
        },
        headers=auth_header,
    )

    room_id = room_response.json()["id"]
    assert room_response.status_code == 201

    # Second user becomes member in room
    auth_header_user2 = await _register_and_login(
        client,
        username="user2",
        email="user2@example.com",
    )
    user_response = await client.post(
        f"/rooms/{room_id}/join", headers=auth_header_user2
    )
    assert user_response.status_code == 200

    # Second user sends message
    message = "Hello world!"
    response = await client.post(
        f"/rooms/{room_id}/messages",
        headers=auth_header_user2,
        json={"content": message},
    )
    assert response.status_code == 201
    assert response.json()["content"] == message

    # Second user can list messages
    response = await client.get(
        f"/rooms/{room_id}/messages",
        headers=auth_header_user2,
    )
    message_list = response.json()
    assert len(message_list) == 1
    assert message_list[0]["content"] == message
