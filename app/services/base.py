import uuid
from typing import Generic, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.repositories.base import BaseRepository

ModelT = TypeVar("ModelT", bound=Base)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)


class BaseService(Generic[ModelT, CreateSchemaT, UpdateSchemaT]):
    entity_name = "resource"

    def __init__(self, session: AsyncSession, repository: BaseRepository[ModelT]) -> None:
        self.session = session
        self.repository = repository

    async def list(self) -> list[ModelT]:
        return await self.repository.list()

    async def get(self, entity_id: uuid.UUID) -> ModelT:
        entity = await self.repository.get(entity_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found",
            )
        return entity

    async def create(self, payload: CreateSchemaT) -> ModelT:
        entity = await self.repository.create(payload.model_dump())
        await self.session.commit()
        return entity

    async def update(self, entity_id: uuid.UUID, payload: UpdateSchemaT) -> ModelT:
        entity = await self.get(entity_id)
        updated = await self.repository.update(entity, payload.model_dump(exclude_unset=True))
        await self.session.commit()
        return updated

    async def delete(self, entity_id: uuid.UUID) -> None:
        entity = await self.get(entity_id)
        await self.repository.delete(entity)
        await self.session.commit()

    async def ensure_exists(self, model: type[Base], entity_id: uuid.UUID, name: str) -> Base:
        entity = await self.session.get(model, entity_id)
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{name} not found",
            )
        return entity
