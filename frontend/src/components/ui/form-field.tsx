import { ReactNode } from "react";

interface FormFieldProps {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}

export function FormField({ label, htmlFor, hint, error, children }: FormFieldProps): JSX.Element {
  return (
    <label className="ui-field" htmlFor={htmlFor}>
      <span>{label}</span>
      {children}
      {hint ? <small className="ui-field__hint">{hint}</small> : null}
      {error ? <small className="ui-field__error">{error}</small> : null}
    </label>
  );
}
