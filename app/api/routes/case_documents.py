import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.document import DocumentRead
from app.services.document_management import DocumentManagementService

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["case-documents"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_case_document(
    case_id: uuid.UUID,
    session: SessionDep,
    uploaded_by_user_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    document_status: Annotated[str, Form()] = "uploaded",
    classification_label: Annotated[str | None, Form()] = None,
    classification_source: Annotated[str | None, Form()] = None,
    _: Annotated[object, Depends(authorize_case_access(Permission.MANAGE_DOCUMENTS))] = None,
) -> DocumentRead:
    return await DocumentManagementService(session).upload_document(
        case_id=case_id,
        uploaded_by_user_id=uploaded_by_user_id,
        file=file,
        document_status=document_status,
        classification_label=classification_label,
        classification_source=classification_source,
    )


@router.get("", response_model=list[DocumentRead])
async def list_case_documents(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.VIEW_DOCUMENTS))],
) -> list[DocumentRead]:
    return await DocumentManagementService(session).list_case_documents(case_id)
