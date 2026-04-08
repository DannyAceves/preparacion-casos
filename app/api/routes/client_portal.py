import uuid
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import authorize_case_access
from app.api.deps import get_session_dependency
from app.core.rbac import Permission
from app.schemas.case_questionnaire import CaseQuestionnaireAnswerUpdateRequest, QuestionnaireAnswerRead
from app.schemas.client_portal import (
    ClientPortalAccessRead,
    ClientPortalContextRead,
    ClientPortalDocumentUploadResponse,
    ClientPortalIssueRequest,
    ClientPortalIssuedRead,
    ClientPortalSessionRead,
)
from app.services.client_portal import ClientPortalService

router = APIRouter(tags=["client-portal"])
SessionDep = Annotated[AsyncSession, Depends(get_session_dependency)]


@router.get("/cases/{case_id}/client-portal/access", response_model=ClientPortalAccessRead | None)
async def get_case_client_portal_access(
    case_id: uuid.UUID,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.ISSUE_CLIENT_PORTAL_ACCESS))],
) -> ClientPortalAccessRead | None:
    return await ClientPortalService(session).get_case_portal_access(case_id)


@router.post("/cases/{case_id}/client-portal/access/issue", response_model=ClientPortalIssuedRead)
async def issue_case_client_portal_access(
    case_id: uuid.UUID,
    payload: ClientPortalIssueRequest,
    session: SessionDep,
    _: Annotated[object, Depends(authorize_case_access(Permission.ISSUE_CLIENT_PORTAL_ACCESS))],
) -> ClientPortalIssuedRead:
    return await ClientPortalService(session).issue_case_portal_access(case_id, payload)


@router.post("/client-portal/access/context", response_model=ClientPortalContextRead)
async def get_client_portal_context(
    session: SessionDep,
    token: Annotated[str | None, Form()] = None,
    passcode: Annotated[str | None, Form()] = None,
    portal_session_token: Annotated[str | None, Form()] = None,
) -> ClientPortalContextRead:
    return await ClientPortalService(session).get_portal_context(token, passcode, portal_session_token)


@router.post("/client-portal/access/authenticate", response_model=ClientPortalSessionRead)
async def authenticate_client_portal_access(
    token: Annotated[str, Form()],
    passcode: Annotated[str, Form()],
    session: SessionDep,
) -> ClientPortalSessionRead:
    return await ClientPortalService(session).authenticate_portal(token, passcode)


@router.post("/client-portal/access/questionnaire/answers", response_model=QuestionnaireAnswerRead, status_code=status.HTTP_201_CREATED)
async def create_client_portal_questionnaire_answer(
    session: SessionDep,
    question_id: Annotated[uuid.UUID, Form()],
    token: Annotated[str | None, Form()] = None,
    passcode: Annotated[str | None, Form()] = None,
    portal_session_token: Annotated[str | None, Form()] = None,
    answer_text: Annotated[str | None, Form()] = None,
    answer_date: Annotated[str | None, Form()] = None,
    answer_boolean: Annotated[bool | None, Form()] = None,
    answer_choice: Annotated[str | None, Form()] = None,
    answer_choices: Annotated[str | None, Form()] = None,
    answer_json: Annotated[str | None, Form()] = None,
) -> QuestionnaireAnswerRead:
    value: dict[str, object] = {}
    if answer_text is not None:
        value["answer_text"] = answer_text
    if answer_date is not None:
        value["answer_date"] = answer_date
    if answer_boolean is not None:
        value["answer_boolean"] = answer_boolean
    if answer_choice is not None:
        value["answer_choice"] = answer_choice
    if answer_choices is not None:
        value["answer_choices"] = [item.strip() for item in answer_choices.split(",") if item.strip()]
    if answer_json is not None:
        value["answer_json"] = json.loads(answer_json)
    return await ClientPortalService(session).save_answer(token, passcode, question_id, value, portal_session_token)


@router.patch("/client-portal/access/questionnaire/answers/{answer_id}", response_model=QuestionnaireAnswerRead)
async def update_client_portal_questionnaire_answer(
    answer_id: uuid.UUID,
    session: SessionDep,
    token: Annotated[str | None, Form()] = None,
    passcode: Annotated[str | None, Form()] = None,
    portal_session_token: Annotated[str | None, Form()] = None,
    answer_text: Annotated[str | None, Form()] = None,
    answer_date: Annotated[str | None, Form()] = None,
    answer_boolean: Annotated[bool | None, Form()] = None,
    answer_choice: Annotated[str | None, Form()] = None,
    answer_choices: Annotated[str | None, Form()] = None,
    answer_json: Annotated[str | None, Form()] = None,
) -> QuestionnaireAnswerRead:
    value: dict[str, object] = {}
    if answer_text is not None:
        value["answer_text"] = answer_text
    if answer_date is not None:
        value["answer_date"] = answer_date
    if answer_boolean is not None:
        value["answer_boolean"] = answer_boolean
    if answer_choice is not None:
        value["answer_choice"] = answer_choice
    if answer_choices is not None:
        value["answer_choices"] = [item.strip() for item in answer_choices.split(",") if item.strip()]
    if answer_json is not None:
        value["answer_json"] = json.loads(answer_json)
    return await ClientPortalService(session).update_answer(
        token,
        passcode,
        answer_id,
        CaseQuestionnaireAnswerUpdateRequest(value=value),
        portal_session_token,
    )


@router.post("/client-portal/access/documents/upload", response_model=ClientPortalDocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_client_portal_document(
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    token: Annotated[str | None, Form()] = None,
    passcode: Annotated[str | None, Form()] = None,
    portal_session_token: Annotated[str | None, Form()] = None,
    document_type: Annotated[str | None, Form()] = None,
    checklist_item_id: Annotated[uuid.UUID | None, Form()] = None,
) -> ClientPortalDocumentUploadResponse:
    return await ClientPortalService(session).upload_document(
        token=token,
        passcode=passcode,
        portal_session_token=portal_session_token,
        file=file,
        document_type=document_type,
        checklist_item_id=checklist_item_id,
    )
