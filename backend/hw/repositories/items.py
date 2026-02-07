from database import db
from typing import Optional


class ItemRepository:
    async def get_by_item_id(self, item_id: int) -> Optional[dict]:
        row = await db.fetchrow(
            """
            SELECT 
                i.id, i.item_id, i.seller_id, i.name, i.description, 
                i.category, i.images_qty, i.created_at,
                u.is_verified_seller
            FROM items i JOIN users u ON i.seller_id = u.seller_id
            WHERE i.item_id = $1
            """,
            item_id
        )
        if row:
            return dict(row)
        return None

    async def create(self, item_id: int, seller_id: int, name: str, description: str, category: int, images_qty: int) -> dict:
        row = await db.fetchrow(
            """
            INSERT INTO items (item_id, seller_id, name, description, category, images_qty) 
            VALUES ($1, $2, $3, $4, $5, $6) 
            RETURNING id, item_id, seller_id, name, description, category, images_qty, created_at
            """,
            item_id, seller_id, name, description, category, images_qty
        )
        return dict(row)


item_repository = ItemRepository()