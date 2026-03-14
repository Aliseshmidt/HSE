from typing import Optional, Dict, Any

from app.metrics import DB_QUERY_DURATION_SECONDS
from database import db


class AccountStorage:
    async def create(self, login: str, password: str) -> Dict[str, Any]:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="insert").time():
            row = await db.fetchrow(
                """
                INSERT INTO account (login, password)
                VALUES ($1, $2)
                RETURNING id, login, password, is_blocked
                """,
                login,
                password,
            )
        return dict(row)

    async def get_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="select").time():
            row = await db.fetchrow(
                """
                SELECT id, login, password, is_blocked
                FROM account
                WHERE id = $1
                """,
                account_id,
            )
        return dict(row) if row else None

    async def delete(self, account_id: int) -> None:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="delete").time():
            await db.execute(
                """
                DELETE FROM account
                WHERE id = $1
                """,
                account_id,
            )

    async def block(self, account_id: int) -> Optional[Dict[str, Any]]:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="update").time():
            row = await db.fetchrow(
                """
                UPDATE account
                SET is_blocked = TRUE
                WHERE id = $1
                RETURNING id, login, password, is_blocked
                """,
                account_id,
            )
        return dict(row) if row else None

    async def get_by_login_and_password(
        self,
        login: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="select").time():
            row = await db.fetchrow(
                """
                SELECT id, login, password, is_blocked
                FROM account
                WHERE login = $1 AND password = $2
                """,
                login,
                password,
            )
        return dict(row) if row else None


account_storage = AccountStorage()

