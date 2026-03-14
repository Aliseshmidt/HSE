import pytest

from account_storage import account_storage
from repositories.accounts import account_repository


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_account_create_and_get_by_id():
    created = await account_repository.create(login="user1", password="pass1")

    assert created["id"] is not None
    assert created["login"] == "user1"
    assert created["password"] == "pass1"
    assert created["is_blocked"] is False

    loaded = await account_repository.get_by_id(created["id"])
    assert loaded == created


@pytest.mark.asyncio
async def test_account_block_marks_as_blocked():
    created = await account_repository.create(login="user2", password="pass2")

    blocked = await account_repository.block(created["id"])
    assert blocked is not None
    assert blocked["id"] == created["id"]
    assert blocked["is_blocked"] is True

    loaded = await account_repository.get_by_id(created["id"])
    assert loaded is not None
    assert loaded["is_blocked"] is True


@pytest.mark.asyncio
async def test_account_delete_removes_account():
    created = await account_repository.create(login="user3", password="pass3")

    await account_repository.delete(created["id"])

    assert await account_repository.get_by_id(created["id"]) is None


@pytest.mark.asyncio
async def test_get_by_login_and_password_works():
    await account_repository.create(login="user4", password="pass4")

    found = await account_repository.get_by_login_and_password(
        login="user4",
        password="pass4",
    )
    assert found is not None
    assert found["login"] == "user4"
    assert found["password"] == "pass4"

    not_found = await account_repository.get_by_login_and_password(
        login="user4",
        password="wrong",
    )
    assert not_found is None

