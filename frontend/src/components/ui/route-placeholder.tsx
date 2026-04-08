import Link from "next/link";

import { Card } from "@/components/ui/card";

interface RoutePlaceholderProps {
  title: string;
  description: string;
  currentFocus: string;
  nextStep: string;
  primaryActionHref?: string;
  primaryActionLabel?: string;
}

export function RoutePlaceholder({
  title,
  description,
  currentFocus,
  nextStep,
  primaryActionHref,
  primaryActionLabel,
}: RoutePlaceholderProps): JSX.Element {
  return (
    <Card title={title} subtitle={description}>
      <div className="route-placeholder">
        <div className="route-placeholder__section">
          <strong>Current focus</strong>
          <p>{currentFocus}</p>
        </div>
        <div className="route-placeholder__section">
          <strong>Next step</strong>
          <p>{nextStep}</p>
        </div>
        {primaryActionHref && primaryActionLabel ? (
          <div className="route-placeholder__actions">
            <Link href={primaryActionHref} className="ui-button">
              {primaryActionLabel}
            </Link>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
