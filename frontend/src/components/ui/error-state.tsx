interface ErrorStateProps {
  title: string;
  description: string;
}

export function ErrorState({ title, description }: ErrorStateProps): JSX.Element {
  return (
    <div className="ui-state ui-state--error">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
