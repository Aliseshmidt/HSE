from database import db
from typing import Optional


class ModerationResultRepository:
    async def create(self, item_id: int) -> dict:
        row = await db.fetchrow(
            """
            INSERT INTO moderation_results (item_id, status)
            VALUES ($1, 'pending')
            RETURNING id, item_id, status, is_violation, probability, 
                     error_message, created_at, processed_at
            """,
            item_id
        )
        return dict(row)

    async def get_by_id(self, moderation_id: int) -> Optional[dict]:
        row = await db.fetchrow(
            """
            SELECT id, item_id, status, is_violation, probability, 
                   error_message, created_at, processed_at
            FROM moderation_results
            WHERE id = $1
            """,
            moderation_id
        )
        if row:
            return dict(row)
        return None

    async def get_latest_by_item_id(self, item_id: int) -> Optional[dict]:
        row = await db.fetchrow(
            """
            SELECT id, item_id, status, is_violation, probability, 
                   error_message, created_at, processed_at
            FROM moderation_results
            WHERE item_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            item_id
        )
        if row:
            return dict(row)
        return None

    async def update_status(
        self,
        moderation_id: int,
        status: str,
        is_violation: Optional[bool] = None,
        probability: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Optional[dict]:
        updates = ["status = $2"]
        params = [moderation_id, status]
        param_index = 3

        if is_violation is not None:
            updates.append(f"is_violation = ${param_index}")
            params.append(is_violation)
            param_index += 1

        if probability is not None:
            updates.append(f"probability = ${param_index}")
            params.append(probability)
            param_index += 1

        if error_message is not None:
            updates.append(f"error_message = ${param_index}")
            params.append(error_message)
            param_index += 1

        if status != 'pending':
            updates.append("processed_at = CURRENT_TIMESTAMP")

        query = f"""
            UPDATE moderation_results
            SET {', '.join(updates)}
            WHERE id = $1
            RETURNING id, item_id, status, is_violation, probability, 
                     error_message, created_at, processed_at
        """

        row = await db.fetchrow(query, *params)
        if row:
            return dict(row)
        return None


moderation_result_repository = ModerationResultRepository()

