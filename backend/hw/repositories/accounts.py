from typing import Optional, Dict, Any

from account_storage import account_storage, AccountStorage


class AccountRepository:
    def __init__(self, storage: AccountStorage = account_storage):
        self._storage = storage

    async def create(self, login: str, password: str) -> Dict[str, Any]:
        return await self._storage.create(login=login, password=password)

    async def get_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        return await self._storage.get_by_id(account_id=account_id)

    async def delete(self, account_id: int) -> None:
        await self._storage.delete(account_id=account_id)

    async def block(self, account_id: int) -> Optional[Dict[str, Any]]:
        return await self._storage.block(account_id=account_id)

    async def get_by_login_and_password(
        self,
        login: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        return await self._storage.get_by_login_and_password(
            login=login,
            password=password,
        )


account_repository = AccountRepository()

