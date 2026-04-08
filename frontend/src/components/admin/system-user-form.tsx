"use client";

import { FormEvent, useMemo, useState } from "react";

import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import { createSystemUser, updateSystemUser } from "@/services/system-users";
import { InternalRole } from "@/types/auth";
import { SystemUser } from "@/types/system-user";

interface SystemUserFormProps {
  mode: "create" | "edit";
  initialUser?: SystemUser | null;
  onSaved: (user: SystemUser) => Promise<void> | void;
  onCancel: () => void;
}

interface FormState {
  firstName: string;
  lastName: string;
  email: string;
  role: InternalRole;
  isActive: boolean;
}

interface FormErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
}

const roleOptions: InternalRole[] = ["admin", "reception", "attorney", "paralegal", "client"];

function getInitialState(user?: SystemUser | null): FormState {
  return {
    firstName: user?.first_name ?? "",
    lastName: user?.last_name ?? "",
    email: user?.email ?? "",
    role: user?.role ?? "paralegal",
    isActive: user?.is_active ?? true,
  };
}

function validate(values: FormState): FormErrors {
  const errors: FormErrors = {};
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

export function SystemUserForm({ mode, initialUser, onSaved, onCancel }: SystemUserFormProps): JSX.Element {
  const [values, setValues] = useState<FormState>(() => getInitialState(initialUser));
  const [errors, setErrors] = useState<FormErrors>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitLabel = useMemo(() => {
    if (mode === "create") {
      return isSubmitting ? "Creating user..." : "Create User";
    }
    return isSubmitting ? "Saving user..." : "Save Changes";
  }, [isSubmitting, mode]);

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
      const payload = {
        first_name: values.firstName.trim(),
        last_name: values.lastName.trim(),
        email: values.email.trim(),
        role: values.role,
        is_active: values.isActive,
      };

      const savedUser =
        mode === "create"
          ? await createSystemUser(payload)
          : await updateSystemUser(initialUser!.id, payload);

      setSuccessMessage(
        mode === "create"
          ? `User ${savedUser.first_name} ${savedUser.last_name} created successfully.`
          : `User ${savedUser.first_name} ${savedUser.last_name} updated successfully.`,
      );
      await onSaved(savedUser);
      if (mode === "create") {
        setValues(getInitialState(null));
      }
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, mode === "create" ? "Could not create the user." : "Could not update the user."),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function updateField<Key extends keyof FormState>(field: Key, value: FormState[Key]): void {
    setValues((current) => ({ ...current, [field]: value }));
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <div className="entity-form__grid">
        <FormField label="First name" htmlFor="system-user-first-name" error={errors.firstName}>
          <input
            id="system-user-first-name"
            value={values.firstName}
            onChange={(event) => updateField("firstName", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Last name" htmlFor="system-user-last-name" error={errors.lastName}>
          <input
            id="system-user-last-name"
            value={values.lastName}
            onChange={(event) => updateField("lastName", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Email" htmlFor="system-user-email" error={errors.email}>
          <input
            id="system-user-email"
            type="email"
            value={values.email}
            onChange={(event) => updateField("email", event.target.value)}
            disabled={isSubmitting}
          />
        </FormField>

        <FormField label="Role" htmlFor="system-user-role">
          <select
            id="system-user-role"
            value={values.role}
            onChange={(event) => updateField("role", event.target.value as InternalRole)}
            disabled={isSubmitting}
          >
            {roleOptions.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </FormField>

        <FormField label="Status" htmlFor="system-user-status" hint="Inactive users stay listed but lose access.">
          <select
            id="system-user-status"
            value={values.isActive ? "active" : "inactive"}
            onChange={(event) => updateField("isActive", event.target.value === "active")}
            disabled={isSubmitting}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </FormField>
      </div>

      {successMessage ? <FormFeedback tone="success" message={successMessage} /> : null}
      {errorMessage ? <FormFeedback tone="error" message={errorMessage} /> : null}

      <div className="entity-form__actions">
        <button type="submit" className="ui-button" disabled={isSubmitting}>
          {submitLabel}
        </button>
        <button type="button" className="ui-button ui-button--ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
