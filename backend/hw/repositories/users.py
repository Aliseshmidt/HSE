from database import db
from typing import Optional

from app.metrics import DB_QUERY_DURATION_SECONDS


class UserRepository:
    async def get_by_seller_id(self, seller_id: int) -> Optional[dict]:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="select").time():
            row = await db.fetchrow(
                "SELECT id, seller_id, is_verified_seller, created_at FROM users WHERE seller_id = $1",
                seller_id
            )
        if row:
            return dict(row)
        return None

    async def create(self, seller_id: int, is_verified_seller: bool) -> dict:
        with DB_QUERY_DURATION_SECONDS.labels(query_type="insert").time():
            row = await db.fetchrow(
                "INSERT INTO users (seller_id, is_verified_seller) VALUES ($1, $2) RETURNING id, seller_id, is_verified_seller, created_at",
                seller_id,
                is_verified_seller
            )
        return dict(row)


user_repository = UserRepository()