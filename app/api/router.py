from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.case_documents import router as case_documents_router
from app.api.routes.case_document_checklist import router as case_document_checklist_router
from app.api.routes.client_portal import router as client_portal_router
from app.api.routes.case_forms import router as case_forms_router
from app.api.routes.case_packets import router as case_packets_router
from app.api.routes.case_questionnaires import router as case_questionnaires_router
from app.api.routes.case_readiness import router as case_readiness_router
from app.api.routes.case_submissions import router as case_submissions_router
from app.api.routes.canonical_fields import router as canonical_fields_router
from app.api.routes.cases import router as cases_router
from app.api.routes.clients import router as clients_router
from app.api.routes.consultations import router as consultations_router
from app.api.routes.documents import router as documents_router
from app.api.routes.generated_forms import router as generated_forms_router
from app.api.routes.inconsistencies import router as inconsistencies_router
from app.api.routes.participants import router as participants_router
from app.api.routes.questionnaire_responses import router as questionnaire_responses_router
from app.api.routes.questionnaire_templates import router as questionnaire_templates_router
from app.api.routes.questionnaires import router as questionnaires_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.system_users import router as system_users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(client_portal_router)
api_router.include_router(consultations_router)
api_router.include_router(clients_router)
api_router.include_router(cases_router)
api_router.include_router(case_document_checklist_router)
api_router.include_router(case_documents_router)
api_router.include_router(case_forms_router)
api_router.include_router(case_packets_router)
api_router.include_router(case_questionnaires_router)
api_router.include_router(case_readiness_router)
api_router.include_router(case_submissions_router)
api_router.include_router(participants_router)
api_router.include_router(questionnaire_templates_router)
api_router.include_router(questionnaires_router)
api_router.include_router(questionnaire_responses_router)
api_router.include_router(documents_router)
api_router.include_router(generated_forms_router)
api_router.include_router(canonical_fields_router)
api_router.include_router(inconsistencies_router)
api_router.include_router(reviews_router)
api_router.include_router(audit_logs_router)
api_router.include_router(system_users_router)
