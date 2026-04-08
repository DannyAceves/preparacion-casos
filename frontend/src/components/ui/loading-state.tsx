interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "Loading data..." }: LoadingStateProps): JSX.Element {
  return (
    <div className="ui-state ui-state--loading">
      <span className="ui-spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}
