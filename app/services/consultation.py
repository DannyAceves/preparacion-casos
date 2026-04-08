import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.consultation import Consultation
from app.repositories.case import CaseRepository
from app.repositories.client import ClientRepository
from app.repositories.consultation import ConsultationRepository
from app.schemas.case import CaseRead
from app.schemas.client import ClientRead
from app.schemas.consultation import (
    ConsultationConversionResult,
    ConsultationConvertToCaseRequest,
    ConsultationCreate,
    ConsultationRead,
    ConsultationUpdate,
)
from app.services.base import BaseService

CONVERTIBLE_CONSULTATION_STATUSES = {"approved"}


class ConsultationService(BaseService[Consultation, ConsultationCreate, ConsultationUpdate]):
    entity_name = "consultation"

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, repository=ConsultationRepository(session))
        self.client_repository = ClientRepository(session)
        self.case_repository = CaseRepository(session)

    async def update(self, entity_id: uuid.UUID, payload: ConsultationUpdate) -> Consultation:
        consultation = await self.get(entity_id)
        next_status = payload.status

        if next_status == "converted" and consultation.converted_case_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="consultation can only be marked converted through case conversion",
            )

        if (
            consultation.converted_case_id is not None
            and next_status is not None
            and next_status != "converted"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="converted consultation status cannot be changed back",
            )

        return await super().update(entity_id, payload)

    async def convert_to_case(
        self,
        consultation_id: uuid.UUID,
        payload: ConsultationConvertToCaseRequest,
    ) -> ConsultationConversionResult:
        consultation = await self.get(consultation_id)

        if consultation.converted_case_id is not None and consultation.client_id is not None:
            converted_case = await self.case_repository.get(consultation.converted_case_id)
            client = await self.client_repository.get(consultation.client_id)
            if converted_case is not None and client is not None:
                return ConsultationConversionResult(
                    consultation=ConsultationRead.model_validate(consultation),
                    client=ClientRead.model_validate(client),
                    case=CaseRead.model_validate(converted_case),
                )

        if consultation.status not in CONVERTIBLE_CONSULTATION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="consultation must be approved before converting to a case",
            )

        case_type = payload.case_type or consultation.suggested_case_type
        if not case_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="case_type is required to convert consultation into a case",
            )

        client = await self.client_repository.find_by_email(consultation.email)
        if client is None:
            client = await self.client_repository.create(
                {
                    "first_name": consultation.first_name,
                    "last_name": consultation.last_name,
                    "email": consultation.email,
                    "phone": consultation.phone,
                    "date_of_birth": consultation.date_of_birth,
                    "notes": consultation.reception_notes,
                }
            )
        else:
            client_update_data = {}
            if not client.phone and consultation.phone:
                client_update_data["phone"] = consultation.phone
            if not client.date_of_birth and consultation.date_of_birth:
                client_update_data["date_of_birth"] = consultation.date_of_birth
            if consultation.reception_notes and consultation.reception_notes != client.notes:
                client_update_data["notes"] = consultation.reception_notes
            if client_update_data:
                client = await self.client_repository.update(client, client_update_data)

        created_case = await self.case_repository.create(
            {
                "client_id": client.id,
                "case_number": payload.case_number,
                "case_type": case_type,
                "status": "draft",
                "title": payload.title,
                "summary": payload.summary or consultation.reception_notes,
            }
        )

        updated_consultation = await self.repository.update(
            consultation,
            {
                "client_id": client.id,
                "converted_case_id": created_case.id,
                "status": "converted",
            },
        )

        await self.session.commit()

        return ConsultationConversionResult(
            consultation=ConsultationRead.model_validate(updated_consultation),
            client=ClientRead.model_validate(client),
            case=CaseRead.model_validate(created_case),
        )
