"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import { createCase } from "@/services/cases";
import { Case } from "@/types/case";
import { Client } from "@/types/client";

interface CreateCaseFormProps {
  clients: Client[];
  initialClientId?: string | null;
  onCreated: (caseItem: Case) => Promise<void> | void;
  onCancel: () => void;
}

interface CreateCaseFormState {
  clientId: string;
  caseNumber: string;
  caseType: string;
  title: string;
  summary: string;
}

interface CaseFormErrors {
  clientId?: string;
  caseNumber?: string;
  caseType?: string;
  title?: string;
}

const defaultCaseTypes = ["family-based", "employment-based", "humanitarian"];

function validate(values: CreateCaseFormState): CaseFormErrors {
  const errors: CaseFormErrors = {};
  if (!values.clientId) {
    errors.clientId = "Select an existing client.";
  }
  if (!values.caseNumber.trim()) {
    errors.caseNumber = "Case number is required.";
  }
  if (!values.caseType.trim()) {
    errors.caseType = "Case type is required.";
  }
  if (!values.title.trim()) {
    errors.title = "Title is required.";
  }
  return errors;
}

export function CreateCaseForm({
  clients,
  initialClientId,
  onCreated,
  onCancel,
}: CreateCaseFormProps): JSX.Element {
  const router = useRouter();
  const [values, setValues] = useState<CreateCaseFormState>({
    clientId: initialClientId ?? "",
    caseNumber: "",
    caseType: defaultCaseTypes[0],
    title: "",
    summary: "",
  });
  const [errors, setErrors] = useState<CaseFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const clientOptions = useMemo(
    () =>
      clients
        .map((client) => ({
          id: client.id,
          label: `${client.first_name} ${client.last_name}`.trim(),
          email: client.email,
        }))
        .sort((left, right) => left.label.localeCompare(right.label)),
    [clients],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const validationErrors = validate(values);
    setErrors(validationErrors);
    setErrorMessage(null);
    setSuccessMessage(null);

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      const createdCase = await createCase({
        client_id: values.clientId,
        case_number: values.caseNumber.trim(),
        case_type: values.caseType.trim(),
        title: values.title.trim(),
        summary: values.summary.trim() || null,
      });
      setSuccessMessage(`Case ${createdCase.case_number} created successfully. Redirecting...`);
      await onCreated(createdCase);
      router.push(`/cases/${createdCase.id}`);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "Could not create the case."));
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateField<Key extends keyof CreateCaseFormState>(field: Key, value: CreateCaseFormState[Key]): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  const hasClients = clientOptions.length > 0;

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <div className="entity-form__grid">
        <FormField
          label="Client"
          htmlFor="case-client-id"
          hint={!hasClients ? "Create a client first to open a case." : undefined}
          error={errors.clientId}
        >
          <select
            id="case-client-id"
            value={values.clientId}
            onChange={(event) => updateField("clientId", event.target.value)}
            disabled={isSubmitting || !hasClients}
          >
            <option value="">{hasClients ? "Select a client" : "No clients available"}</option>
            {clientOptions.map((client) => (
              <option key={client.id} value={client.id}>
                {client.label} · {client.email}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Case number" htmlFor="case-number" error={errors.caseNumber}>
          <input
            id="case-number"
            value={values.caseNumber}
            onChange={(event) => updateField("caseNumber", event.target.value)}
            disabled={isSubmitting}
            placeholder="CASE-2026-001"
          />
        </FormField>

        <FormField label="Case type" htmlFor="case-type" error={errors.caseType}>
          <input
            id="case-type"
            list="case-type-options"
            value={values.caseType}
            onChange={(event) => updateField("caseType", event.target.value)}
            disabled={isSubmitting}
            placeholder="family-based"
          />
          <datalist id="case-type-options">
            {defaultCaseTypes.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
        </FormField>

        <FormField label="Title" htmlFor="case-title" error={errors.title}>
          <input
            id="case-title"
            value={values.title}
            onChange={(event) => updateField("title", event.target.value)}
            disabled={isSubmitting}
            placeholder="Adjustment of status for principal applicant"
          />
        </FormField>

        <FormField label="Summary" htmlFor="case-summary" hint="Optional operational context for the staff team.">
          <textarea
            id="case-summary"
            className="ui-textarea"
            value={values.summary}
            onChange={(event) => updateField("summary", event.target.value)}
            disabled={isSubmitting}
            rows={4}
          />
        </FormField>
      </div>

      {successMessage ? <FormFeedback tone="success" message={successMessage} /> : null}
      {errorMessage ? <FormFeedback tone="error" message={errorMessage} /> : null}

      <div className="entity-form__actions">
        <button type="submit" className="ui-button" disabled={isSubmitting || !hasClients}>
          {isSubmitting ? "Creating case..." : "Create Case"}
        </button>
        <button type="button" className="ui-button ui-button--ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
