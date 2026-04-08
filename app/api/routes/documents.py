import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_document_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.document import DocumentClassificationUpdate, DocumentDetailRead, DocumentRead, DocumentReprocessRequest
from app.services.document_management import DocumentManagementService

router = APIRouter(prefix="/documents", tags=["documents"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]

@router.get("/{document_id}", response_model=DocumentDetailRead)
async def get_document(
    document_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_document_access(Permission.VIEW_DOCUMENTS))],
) -> DocumentDetailRead:
    return await DocumentManagementService(session).get_document_detail(document_id)


@router.post("/{document_id}/replace", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def replace_document(
    document_id: uuid.UUID,
    session: SessionDep,
    uploaded_by_user_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    document_status: Annotated[str | None, Form()] = None,
    replacement_notes: Annotated[str | None, Form()] = None,
    _: Annotated[object, Depends(authorize_document_access(Permission.MANAGE_DOCUMENTS))] = None,
) -> DocumentRead:
    return await DocumentManagementService(session).replace_document(
        document_id=document_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file=file,
        document_status=document_status,
        replacement_notes=replacement_notes,
    )


@router.patch("/{document_id}/classification", response_model=DocumentRead)
async def update_document_classification(
    document_id: uuid.UUID,
    payload: DocumentClassificationUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_document_access(Permission.REVIEW_DOCUMENT_EXTRACTION))],
) -> DocumentRead:
    return await DocumentManagementService(session).update_classification(document_id, payload)


@router.post("/{document_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document(
    document_id: uuid.UUID,
    payload: DocumentReprocessRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_document_access(Permission.MANAGE_DOCUMENTS))],
) -> dict[str, str]:
    await DocumentManagementService(session).enqueue_reprocessing(
        document_id=document_id,
        actor_reference=payload.actor_reference,
    )
    await session.commit()
    return {"status": "queued"}
