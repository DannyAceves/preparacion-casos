import uuid
from typing import Generic, TypeVar

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    def base_query(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    async def list(self) -> list[ModelT]:
        order_column = getattr(self.model, "created_at", None)
        query = self.base_query().order_by(desc(order_column)) if order_column is not None else self.base_query()
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def create(self, data: dict) -> ModelT:
        entity = self.model(**data)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelT, data: dict) -> ModelT:
        for field, value in data.items():
            setattr(entity, field, value)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
