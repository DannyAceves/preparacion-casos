import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.participant import Participant
from app.models.case import Case
from app.repositories.participant import ParticipantRepository
from app.schemas.participant import ParticipantCreate, ParticipantUpdate
from app.services.base import BaseService


class ParticipantService(BaseService[Participant, ParticipantCreate, ParticipantUpdate]):
    entity_name = "participant"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=ParticipantRepository(session))

    async def create(self, payload: ParticipantCreate) -> Participant:
        await self.ensure_exists(Case, payload.case_id, "case")
        return await super().create(payload)

    async def update(self, entity_id: uuid.UUID, payload: ParticipantUpdate) -> Participant:
        if payload.case_id is not None:
            await self.ensure_exists(Case, payload.case_id, "case")
        return await super().update(entity_id, payload)
