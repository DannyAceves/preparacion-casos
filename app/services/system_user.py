import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_user import SystemUser
from app.repositories.system_user import SystemUserRepository
from app.schemas.system_user import SystemUserCreate, SystemUserListFilters, SystemUserUpdate
from app.services.base import BaseService


class SystemUserService(BaseService[SystemUser, SystemUserCreate, SystemUserUpdate]):
    entity_name = "system user"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=SystemUserRepository(session))
        self.repository: SystemUserRepository

    async def list_filtered(self, filters: SystemUserListFilters) -> list[SystemUser]:
        return await self.repository.list_filtered(
            search=filters.search,
            role=filters.role,
            is_active=filters.is_active,
        )

    async def create(self, payload: SystemUserCreate) -> SystemUser:
        existing = await self.repository.find_by_email(payload.email)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user email already exists")
        return await super().create(payload)

    async def update(self, entity_id: uuid.UUID, payload: SystemUserUpdate) -> SystemUser:
        updates = payload.model_dump(exclude_unset=True)
        if "email" in updates:
            existing = await self.repository.find_by_email(str(updates["email"]))
            if existing is not None and existing.id != entity_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user email already exists")

        entity = await self.get(entity_id)
        updated = await self.repository.update(entity, updates)
        await self.session.commit()
        return updated

    async def authenticate_by_email(self, email: str) -> SystemUser:
        user = await self.repository.find_by_email(email)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No active user found for this email.",
            )

        updated = await self.repository.update(
            user,
            {
                "last_login_at": datetime.now(timezone.utc),
            },
        )
        await self.session.commit()
        return updated
