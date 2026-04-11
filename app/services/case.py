import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.client import Client
from app.repositories.case import CaseRepository
from app.schemas.case import CaseCreate, CaseUpdate
from app.schemas.case_readiness import CaseTransitionRequest
from app.services.base import BaseService
from app.services.case_readiness import CaseReadinessService

MONITORED_CASE_STATUSES = {"attorney_review", "ready_for_submission", "submitted"}


class CaseService(BaseService[Case, CaseCreate, CaseUpdate]):
    entity_name = "case"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=CaseRepository(session))

    async def create(self, payload: CaseCreate) -> Case:
        await self.ensure_exists(Client, payload.client_id, "client")
        return await super().create(payload)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Case]:
        return await self.repository.list(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update(self, entity_id: uuid.UUID, payload: CaseUpdate) -> Case:
        if payload.client_id is not None:
            await self.ensure_exists(Client, payload.client_id, "client")
        current_case = await self.get(entity_id)
        update_data = payload.model_dump(exclude_unset=True)

        next_status = update_data.pop("status", None)
        if next_status in MONITORED_CASE_STATUSES and next_status != current_case.status:
            current_case = await CaseReadinessService(self.session).transition_case(
                entity_id,
                CaseTransitionRequest(target_status=next_status),
            )
        elif next_status is not None:
            update_data["status"] = next_status

        if not update_data:
            return current_case

        updated = await self.repository.update(current_case, update_data)
        await self.session.commit()
        return updated
