"use client";

import { FormEvent, useState } from "react";

import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import { createClient } from "@/services/clients";
import { Client } from "@/types/client";

interface CreateClientFormProps {
  onCreated: (client: Client) => Promise<void> | void;
  onCancel: () => void;
}

interface CreateClientFormState {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  notes: string;
}

interface ClientFormErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
}

const initialState: CreateClientFormState = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  dateOfBirth: "",
  notes: "",
};

function validate(values: CreateClientFormState): ClientFormErrors {
  const errors: ClientFormErrors = {};
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

export function CreateClientForm({ onCreated, onCancel }: CreateClientFormProps): JSX.Element {
  const [values, setValues] = useState<CreateClientFormState>(initialState);
  const [errors, setErrors] = useState<ClientFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
      const client = await createClient({
        first_name: values.firstName.trim(),
        last_name: values.lastName.trim(),
        email: values.email.trim(),
        phone: values.phone.trim() || null,
        date_of_birth: values.dateOfBirth || null,
        notes: values.notes.trim() || null,
      });
      setValues(initialState);
      setErrors({});
      setSuccessMessage(`Client ${client.first_name} ${client.last_name} created successfully.`);
      await onCreated(client);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "Could not create the client."));
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateField<Key extends keyof CreateClientFormState>(field: Key, value: CreateClientFormState[Key]): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <div className="entity-form__grid">
        <FormField label="First name" htmlFor="client-first-name" error={errors.firstName}>
          <input
            id="client-first-name"
            value={values.firstName}
            onChange={(event) => updateField("firstName", event.target.value)}
            disabled={isSubmitting}
            autoComplete="given-name"
          />
        </FormField>

        <FormField label="Last name" htmlFor="client-last-name" error={errors.lastName}>
          <input
            id="client-last-name"
            value={values.lastName}
            onChange={(event) => updateField("lastName", event.target.value)}
            disabled={isSubmitting}
            autoComplete="family-name"
          />
        </FormField>

        <FormField label="Email" htmlFor="client-email" error={errors.email}>
          <input
            id="client-email"
            type="email"
            value={values.email}
            onChange={(event) => updateField("email", event.target.value)}
            disabled={isSubmitting}
            autoComplete="email"
          />
        </FormField>

        <FormField label="Phone" htmlFor="client-phone">
          <input
            id="client-phone"
            value={values.phone}
            onChange={(event) => updateField("phone", event.target.value)}
            disabled={isSubmitting}
            autoComplete="tel"
          />
        </FormField>

        <FormField label="Date of birth" htmlFor="client-date-of-birth">
          <input
            id="client-date-of-birth"
            type="date"
            value={values.dateOfBirth}
            onChange={(event) => updateField("dateOfBirth", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Notes" htmlFor="client-notes" hint="Optional context for intake or follow-up.">
          <textarea
            id="client-notes"
            className="ui-textarea"
            value={values.notes}
            onChange={(event) => updateField("notes", event.target.value)}
            disabled={isSubmitting}
            rows={4}
          />
        </FormField>
      </div>

      {successMessage ? <FormFeedback tone="success" message={successMessage} /> : null}
      {errorMessage ? <FormFeedback tone="error" message={errorMessage} /> : null}

      <div className="entity-form__actions">
        <button type="submit" className="ui-button" disabled={isSubmitting}>
          {isSubmitting ? "Creating client..." : "Create Client"}
        </button>
        <button type="button" className="ui-button ui-button--ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
