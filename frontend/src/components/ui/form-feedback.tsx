interface FormFeedbackProps {
  tone: "success" | "error";
  message: string;
}

export function FormFeedback({ tone, message }: FormFeedbackProps): JSX.Element {
  return <p className={`document-feedback document-feedback--${tone}`}>{message}</p>;
}
