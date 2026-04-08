"use client";

import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { ApiErrorPayload } from "@/types/api";
import { TimelineEventRecord } from "@/types/workspace";

interface TimelinePanelProps {
  timeline: TimelineEventRecord[];
  loading: boolean;
  error: ApiErrorPayload | null;
}

function formatPayload(payload: TimelineEventRecord["payload"]): string | null {
  if (!payload) {
    return null;
  }

  return JSON.stringify(payload, null, 2);
}

export function TimelinePanel({ timeline, loading, error }: TimelinePanelProps): JSX.Element {
  if (loading) {
    return <LoadingState label="Loading timeline..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load timeline"
        description="The case timeline could not be retrieved from the backend."
      />
    );
  }

  if (!timeline.length) {
    return (
      <EmptyState
        title="No timeline events"
        description="Audit logs and reviews will appear here as the case moves through the workflow."
      />
    );
  }

  const orderedTimeline = [...timeline].sort(
    (left, right) => new Date(right.occurred_at).getTime() - new Date(left.occurred_at).getTime(),
  );

  return (
    <div className="page-stack">
      {orderedTimeline.map((event) => {
        const payload = formatPayload(event.payload);

        return (
          <div key={event.id} className="entity-card">
            <div className="entity-card__header entity-card__header--spread">
              <div>
                <strong>{event.action}</strong>
                <p>
                  {event.entity_type} | {event.event_type}
                </p>
              </div>
              <div className="entity-card__meta">
                <p>{new Date(event.occurred_at).toLocaleString()}</p>
                <p>{event.actor_reference ?? "System"}</p>
              </div>
            </div>

            <div className="entity-card__meta">
              <p>Entity ID: {event.entity_id}</p>
            </div>

            {payload ? <pre className="entity-card__evidence">{payload}</pre> : <p className="entity-card__hint">No payload attached.</p>}
          </div>
        );
      })}
    </div>
  );
}
