"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Card } from "@/components/ui/card";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { usePermissions } from "@/hooks/use-permissions";
import { getApiErrorMessage } from "@/lib/api/errors";
import { convertConsultationToCase, updateConsultation } from "@/services/consultations";
import { Consultation } from "@/types/consultation";

interface ConsultationDetailPanelProps {
  initialConsultation: Consultation;
}

interface ConsultationEditState {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  appointmentAt: string;
  assignedAttorney: string;
  suggestedCaseType: string;
  status: string;
  receptionNotes: string;
  intakeAnswers: string;
}

interface ConvertState {
  caseNumber: string;
  title: string;
  caseType: string;
  summary: string;
}

function toDateTimeLocal(value: string | null): string {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  const adjusted = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return adjusted.toISOString().slice(0, 16);
}

function buildEditState(consultation: Consultation): ConsultationEditState {
  return {
    firstName: consultation.first_name,
    lastName: consultation.last_name,
    email: consultation.email,
    phone: consultation.phone ?? "",
    dateOfBirth: consultation.date_of_birth ?? "",
    appointmentAt: toDateTimeLocal(consultation.appointment_at),
    assignedAttorney: consultation.assigned_attorney ?? "",
    suggestedCaseType: consultation.suggested_case_type ?? "",
    status: consultation.status,
    receptionNotes: consultation.reception_notes ?? "",
    intakeAnswers: consultation.intake_answers ?? "",
  };
}

function buildConvertState(consultation: Consultation): ConvertState {
  return {
    caseNumber: "",
    title: `${consultation.suggested_case_type ?? "Consultation"} - ${consultation.first_name} ${consultation.last_name}`.trim(),
    caseType: consultation.suggested_case_type ?? "",
    summary: consultation.reception_notes ?? "",
  };
}

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : "Not scheduled";
}

export function ConsultationDetailPanel({ initialConsultation }: ConsultationDetailPanelProps): JSX.Element {
  const router = useRouter();
  const permissions = usePermissions();
  const [consultation, setConsultation] = useState(initialConsultation);
  const [editValues, setEditValues] = useState<ConsultationEditState>(buildEditState(initialConsultation));
  const [convertValues, setConvertValues] = useState<ConvertState>(buildConvertState(initialConsultation));
  const [saveBusy, setSaveBusy] = useState(false);
  const [convertBusy, setConvertBusy] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [convertError, setConvertError] = useState<string | null>(null);

  const canConvert = useMemo(
    () => consultation.status === "approved" && !consultation.converted_case_id,
    [consultation.converted_case_id, consultation.status],
  );
  const canEditIntake = permissions.role === "admin" || permissions.role === "reception";
  const canConvertToCase =
    permissions.role === "admin" || permissions.role === "attorney" || permissions.role === "paralegal";

  function updateEditField<Key extends keyof ConsultationEditState>(
    field: Key,
    value: ConsultationEditState[Key],
  ): void {
    setEditValues((current) => ({ ...current, [field]: value }));
  }

  function updateConvertField<Key extends keyof ConvertState>(field: Key, value: ConvertState[Key]): void {
    setConvertValues((current) => ({ ...current, [field]: value }));
  }

  async function handleSave(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSaveBusy(true);
    setSaveMessage(null);
    setSaveError(null);

    try {
      const updated = await updateConsultation(consultation.id, {
        first_name: editValues.firstName.trim(),
        last_name: editValues.lastName.trim(),
        email: editValues.email.trim(),
        phone: editValues.phone.trim() || null,
        date_of_birth: editValues.dateOfBirth || null,
        appointment_at: editValues.appointmentAt ? new Date(editValues.appointmentAt).toISOString() : null,
        assigned_attorney: editValues.assignedAttorney.trim() || null,
        suggested_case_type: editValues.suggestedCaseType.trim() || null,
        status: editValues.status,
        reception_notes: editValues.receptionNotes.trim() || null,
        intake_answers: editValues.intakeAnswers.trim() || null,
      });
      setConsultation(updated);
      setEditValues(buildEditState(updated));
      setConvertValues((current) => ({
        ...current,
        caseType: current.caseType || updated.suggested_case_type || "",
        summary: current.summary || updated.reception_notes || "",
      }));
      setSaveMessage("Consultation updated successfully.");
    } catch (error) {
      setSaveError(getApiErrorMessage(error, "Could not update the consultation."));
    } finally {
      setSaveBusy(false);
    }
  }

  async function handleConvert(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setConvertBusy(true);
    setConvertError(null);

    try {
      const result = await convertConsultationToCase(consultation.id, {
        case_number: convertValues.caseNumber.trim(),
        title: convertValues.title.trim(),
        case_type: convertValues.caseType.trim() || null,
        summary: convertValues.summary.trim() || null,
      });
      setConsultation(result.consultation);
      router.push(`/cases/${result.case.id}`);
    } catch (error) {
      setConvertError(getApiErrorMessage(error, "Could not convert the consultation into a case."));
    } finally {
      setConvertBusy(false);
    }
  }

  return (
    <div className="page-stack">
      <div className="case-quick-actions">
        <Link href="/consultations" className="ui-button ui-button--ghost">
          Back To Consultations
        </Link>
        {consultation.converted_case_id ? (
          <Link href={`/cases/${consultation.converted_case_id}`} className="ui-button">
            Open Converted Case
          </Link>
        ) : null}
      </div>

      <div className="case-detail-grid">
        <Card title="Consultation Overview" subtitle="Initial intake and appointment information">
          <dl className="ui-key-values">
            <div>
              <dt>Prospect</dt>
              <dd>{`${consultation.first_name} ${consultation.last_name}`.trim()}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{consultation.status}</dd>
            </div>
            <div>
              <dt>Appointment</dt>
              <dd>{formatDateTime(consultation.appointment_at)}</dd>
            </div>
            <div>
              <dt>Assigned Attorney</dt>
              <dd>{consultation.assigned_attorney ?? "Unassigned"}</dd>
            </div>
            <div>
              <dt>Suggested Case Type</dt>
              <dd>{consultation.suggested_case_type ?? "Not classified"}</dd>
            </div>
            <div>
              <dt>Converted Case</dt>
              <dd>{consultation.converted_case_id ?? "Not converted yet"}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Traceability" subtitle="Links created when intake becomes a formal case">
          <dl className="ui-key-values">
            <div>
              <dt>Consultation ID</dt>
              <dd>{consultation.id}</dd>
            </div>
            <div>
              <dt>Linked Client</dt>
              <dd>{consultation.client_id ?? "Created on conversion"}</dd>
            </div>
            <div>
              <dt>Formal Case</dt>
              <dd>{consultation.converted_case_id ?? "Pending conversion"}</dd>
            </div>
            <div>
              <dt>Last Updated</dt>
              <dd>{new Date(consultation.updated_at).toLocaleString()}</dd>
            </div>
          </dl>
        </Card>
      </div>

      <Card title="Consultation Intake Record" subtitle="Edit appointment details, intake notes and preliminary classification.">
        <form className="entity-form" onSubmit={handleSave}>
          <div className="entity-form__grid">
            <FormField label="First name" htmlFor="detail-first-name">
              <input
                id="detail-first-name"
                value={editValues.firstName}
                onChange={(event) => updateEditField("firstName", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Last name" htmlFor="detail-last-name">
              <input
                id="detail-last-name"
                value={editValues.lastName}
                onChange={(event) => updateEditField("lastName", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Email" htmlFor="detail-email">
              <input
                id="detail-email"
                type="email"
                value={editValues.email}
                onChange={(event) => updateEditField("email", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Phone" htmlFor="detail-phone">
              <input
                id="detail-phone"
                value={editValues.phone}
                onChange={(event) => updateEditField("phone", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Date of birth" htmlFor="detail-date-of-birth">
              <input
                id="detail-date-of-birth"
                type="date"
                value={editValues.dateOfBirth}
                onChange={(event) => updateEditField("dateOfBirth", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Appointment" htmlFor="detail-appointment-at">
              <input
                id="detail-appointment-at"
                type="datetime-local"
                value={editValues.appointmentAt}
                onChange={(event) => updateEditField("appointmentAt", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Assigned attorney" htmlFor="detail-assigned-attorney">
              <input
                id="detail-assigned-attorney"
                value={editValues.assignedAttorney}
                onChange={(event) => updateEditField("assignedAttorney", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Suggested case type" htmlFor="detail-suggested-case-type">
              <input
                id="detail-suggested-case-type"
                value={editValues.suggestedCaseType}
                onChange={(event) => updateEditField("suggestedCaseType", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Status" htmlFor="detail-status" hint="Set to approved before converting into a formal case.">
              <select
                id="detail-status"
                value={editValues.status}
                onChange={(event) => updateEditField("status", event.target.value)}
                disabled={saveBusy || Boolean(consultation.converted_case_id) || !canEditIntake}
              >
                <option value="scheduled">Scheduled</option>
                <option value="intake_in_progress">Intake In Progress</option>
                <option value="approved">Approved</option>
                <option value="converted">Converted</option>
                <option value="closed">Closed</option>
              </select>
            </FormField>
            <FormField label="Reception notes" htmlFor="detail-reception-notes">
              <textarea
                id="detail-reception-notes"
                className="ui-textarea"
                rows={4}
                value={editValues.receptionNotes}
                onChange={(event) => updateEditField("receptionNotes", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
            <FormField label="Pre-intake questionnaire" htmlFor="detail-intake-answers">
              <textarea
                id="detail-intake-answers"
                className="ui-textarea"
                rows={5}
                value={editValues.intakeAnswers}
                onChange={(event) => updateEditField("intakeAnswers", event.target.value)}
                disabled={saveBusy || !canEditIntake}
              />
            </FormField>
          </div>

          {saveMessage ? <FormFeedback tone="success" message={saveMessage} /> : null}
          {saveError ? <FormFeedback tone="error" message={saveError} /> : null}

          <div className="entity-form__actions">
            <button type="submit" className="ui-button" disabled={saveBusy || !canEditIntake}>
              {canEditIntake ? (saveBusy ? "Saving..." : "Save Consultation") : "Editing Restricted"}
            </button>
          </div>
        </form>
      </Card>

      <Card title="Convert To Case" subtitle="Open the formal legal case once the consultation has been approved.">
        {!canConvert && !consultation.converted_case_id ? (
          <p className="entity-card__hint">
            This consultation must be marked as <strong>approved</strong> before it can be converted.
          </p>
        ) : null}
        {!canConvertToCase ? (
          <p className="entity-card__hint">Your role can review intake but cannot convert it into a formal case.</p>
        ) : null}

        {consultation.converted_case_id ? (
          <div className="case-quick-actions">
            <Link href={`/cases/${consultation.converted_case_id}`} className="ui-button">
              Open Converted Case
            </Link>
          </div>
        ) : (
          <form className="entity-form" onSubmit={handleConvert}>
            <div className="entity-form__grid">
              <FormField label="Case number" htmlFor="convert-case-number">
                <input
                  id="convert-case-number"
                  value={convertValues.caseNumber}
                  onChange={(event) => updateConvertField("caseNumber", event.target.value)}
                  disabled={convertBusy}
                  placeholder="CASE-2026-100"
                />
              </FormField>
              <FormField label="Case type" htmlFor="convert-case-type">
                <input
                  id="convert-case-type"
                  value={convertValues.caseType}
                  onChange={(event) => updateConvertField("caseType", event.target.value)}
                  disabled={convertBusy}
                />
              </FormField>
              <FormField label="Case title" htmlFor="convert-title">
                <input
                  id="convert-title"
                  value={convertValues.title}
                  onChange={(event) => updateConvertField("title", event.target.value)}
                  disabled={convertBusy}
                />
              </FormField>
              <FormField label="Case summary" htmlFor="convert-summary">
                <textarea
                  id="convert-summary"
                  className="ui-textarea"
                  rows={4}
                  value={convertValues.summary}
                  onChange={(event) => updateConvertField("summary", event.target.value)}
                  disabled={convertBusy}
                />
              </FormField>
            </div>

            {convertError ? <FormFeedback tone="error" message={convertError} /> : null}

            <div className="entity-form__actions">
              <button type="submit" className="ui-button" disabled={convertBusy || !canConvert || !canConvertToCase}>
                {convertBusy ? "Converting..." : "Convert To Formal Case"}
              </button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}
