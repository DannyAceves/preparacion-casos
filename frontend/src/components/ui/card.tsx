import { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
}

export function Card({ title, subtitle, children }: CardProps): JSX.Element {
  return (
    <section className="ui-card">
      {(title || subtitle) && (
        <header className="ui-card__header">
          {title ? <h3>{title}</h3> : null}
          {subtitle ? <p>{subtitle}</p> : null}
        </header>
      )}
      <div className="ui-card__body">{children}</div>
    </section>
  );
}
