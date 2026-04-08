import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.document_checklist import (
    CaseDocumentChecklistItemCreate,
    CaseDocumentChecklistItemUpdate,
    CaseDocumentChecklistRead,
    CaseDocumentChecklistReorderRequest,
)
from app.services.document_checklist import DocumentChecklistService

router = APIRouter(prefix="/cases/{case_id}/document-checklist", tags=["document-checklist"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("", response_model=CaseDocumentChecklistRead)
async def get_case_document_checklist(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_DOCUMENTS))],
) -> CaseDocumentChecklistRead:
    return await DocumentChecklistService(session).get_case_checklist(case_id)


@router.post("/generate", response_model=CaseDocumentChecklistRead, status_code=status.HTTP_201_CREATED)
async def sync_case_document_checklist(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_DOCUMENT_CHECKLIST))],
) -> CaseDocumentChecklistRead:
    return await DocumentChecklistService(session).sync_case_checklist(case_id)


@router.post("/items", response_model=CaseDocumentChecklistRead, status_code=status.HTTP_201_CREATED)
async def add_case_document_checklist_item(
    case_id: uuid.UUID,
    payload: CaseDocumentChecklistItemCreate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_DOCUMENT_CHECKLIST))],
) -> CaseDocumentChecklistRead:
    return await DocumentChecklistService(session).add_manual_item(case_id, payload)


@router.patch("/items/{item_id}", response_model=CaseDocumentChecklistRead)
async def update_case_document_checklist_item(
    case_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: CaseDocumentChecklistItemUpdate,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_DOCUMENT_CHECKLIST))],
) -> CaseDocumentChecklistRead:
    return await DocumentChecklistService(session).update_item(case_id, item_id, payload)


@router.post("/reorder", response_model=CaseDocumentChecklistRead)
async def reorder_case_document_checklist_items(
    case_id: uuid.UUID,
    payload: CaseDocumentChecklistReorderRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_DOCUMENT_CHECKLIST))],
) -> CaseDocumentChecklistRead:
    return await DocumentChecklistService(session).reorder_items(case_id, payload)
