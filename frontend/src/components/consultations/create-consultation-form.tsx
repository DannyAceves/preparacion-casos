"use client";

import { FormEvent, useState } from "react";

import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import { createConsultation } from "@/services/consultations";
import { Consultation } from "@/types/consultation";

interface CreateConsultationFormProps {
  onCreated: (consultation: Consultation) => Promise<void> | void;
  onCancel: () => void;
}

interface ConsultationFormState {
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

interface ConsultationFormErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
}

const initialState: ConsultationFormState = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  dateOfBirth: "",
  appointmentAt: "",
  assignedAttorney: "",
  suggestedCaseType: "",
  status: "scheduled",
  receptionNotes: "",
  intakeAnswers: "",
};

function validate(values: ConsultationFormState): ConsultationFormErrors {
  const errors: ConsultationFormErrors = {};
  if (!values.firstName.trim()) {
    errors.firstName = "First name is required.";
  }
  if (!values.lastName.trim()) {
    errors.lastName = "Last name is required.";
  }
  if (!values.email.trim()) {
    errors.email = "Email is required.";
  }
  return errors;
}

export function CreateConsultationForm({ onCreated, onCancel }: CreateConsultationFormProps): JSX.Element {
  const [values, setValues] = useState<ConsultationFormState>(initialState);
  const [errors, setErrors] = useState<ConsultationFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function updateField<Key extends keyof ConsultationFormState>(
    field: Key,
    value: ConsultationFormState[Key],
  ): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const validationErrors = validate(values);
    setErrors(validationErrors);
    setSuccessMessage(null);
    setErrorMessage(null);

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      const consultation = await createConsultation({
        first_name: values.firstName.trim(),
        last_name: values.lastName.trim(),
        email: values.email.trim(),
        phone: values.phone.trim() || null,
        date_of_birth: values.dateOfBirth || null,
        appointment_at: values.appointmentAt ? new Date(values.appointmentAt).toISOString() : null,
        assigned_attorney: values.assignedAttorney.trim() || null,
        suggested_case_type: values.suggestedCaseType.trim() || null,
        status: values.status,
        reception_notes: values.receptionNotes.trim() || null,
        intake_answers: values.intakeAnswers.trim() || null,
      });
      setValues(initialState);
      setErrors({});
      setSuccessMessage("Consultation created successfully.");
      await onCreated(consultation);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "Could not create the consultation."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <div className="entity-form__grid">
        <FormField label="First name" htmlFor="consultation-first-name" error={errors.firstName}>
          <input
            id="consultation-first-name"
            value={values.firstName}
            onChange={(event) => updateField("firstName", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Last name" htmlFor="consultation-last-name" error={errors.lastName}>
          <input
            id="consultation-last-name"
            value={values.lastName}
            onChange={(event) => updateField("lastName", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Email" htmlFor="consultation-email" error={errors.email}>
          <input
            id="consultation-email"
            type="email"
            value={values.email}
            onChange={(event) => updateField("email", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Phone" htmlFor="consultation-phone">
          <input
            id="consultation-phone"
            value={values.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Date of birth" htmlFor="consultation-date-of-birth">
          <input
            id="consultation-date-of-birth"
            type="date"
            value={values.dateOfBirth}
            onChange={(event) => updateField("dateOfBirth", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Appointment" htmlFor="consultation-appointment-at">
          <input
            id="consultation-appointment-at"
            type="datetime-local"
            value={values.appointmentAt}
            onChange={(event) => updateField("appointmentAt", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Assigned attorney" htmlFor="consultation-assigned-attorney">
          <input
            id="consultation-assigned-attorney"
            value={values.assignedAttorney}
            onChange={(event) => updateField("assignedAttorney", event.target.value)}
            disabled={isSubmitting}
            placeholder="attorney.name"
          />
        </FormField>

        <FormField label="Suggested case type" htmlFor="consultation-suggested-case-type">
          <input
            id="consultation-suggested-case-type"
            value={values.suggestedCaseType}
            onChange={(event) => updateField("suggestedCaseType", event.target.value)}
            disabled={isSubmitting}
            placeholder="family-based"
          />
        </FormField>

        <FormField label="Status" htmlFor="consultation-status">
          <select
            id="consultation-status"
            value={values.status}
            onChange={(event) => updateField("status", event.target.value)}
            disabled={isSubmitting}
          >
            <option value="scheduled">Scheduled</option>
            <option value="intake_in_progress">Intake In Progress</option>
            <option value="approved">Approved</option>
            <option value="closed">Closed</option>
          </select>
        </FormField>

        <FormField
          label="Reception notes"
          htmlFor="consultation-reception-notes"
          hint="Operational notes from the first call or appointment."
        >
          <textarea
            id="consultation-reception-notes"
            className="ui-textarea"
            rows={4}
            value={values.receptionNotes}
            onChange={(event) => updateField("receptionNotes", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField
          label="Pre-intake questionnaire"
          htmlFor="consultation-intake-answers"
          hint="Freeform pre-questionnaire answers captured during intake."
        >
          <textarea
            id="consultation-intake-answers"
            className="ui-textarea"
            rows={5}
            value={values.intakeAnswers}
            onChange={(event) => updateField("intakeAnswers", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>
      </div>

      {successMessage ? <FormFeedback tone="success" message={successMessage} /> : null}
      {errorMessage ? <FormFeedback tone="error" message={errorMessage} /> : null}

      <div className="entity-form__actions">
        <button type="submit" className="ui-button" disabled={isSubmitting}>
          {isSubmitting ? "Creating consultation..." : "Create Consultation"}
        </button>
        <button type="button" className="ui-button ui-button--ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
