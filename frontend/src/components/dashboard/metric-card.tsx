interface MetricCardProps {
  label: string;
  value: number;
}

export function MetricCard({ label, value }: MetricCardProps): JSX.Element {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
