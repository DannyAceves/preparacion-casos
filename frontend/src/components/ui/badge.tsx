import { ReactNode } from "react";

interface BadgeProps {
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
  children: ReactNode;
}

export function Badge({ tone = "neutral", children }: BadgeProps): JSX.Element {
  return <span className={`ui-badge ui-badge--${tone}`}>{children}</span>;
}
