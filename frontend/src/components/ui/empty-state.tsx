interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps): JSX.Element {
  return (
    <div className="ui-state ui-state--empty">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
