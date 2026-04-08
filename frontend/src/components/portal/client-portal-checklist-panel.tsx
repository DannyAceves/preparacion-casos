import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { CaseDocumentChecklist, CaseDocumentChecklistItem } from "@/types/workspace";

interface ClientPortalChecklistPanelProps {
  checklist: CaseDocumentChecklist;
}

function requirementBadges(item: CaseDocumentChecklistItem): string[] {
  const badges: string[] = [];
  if (item.color_required) badges.push("Color required");
  if (item.english_translation_required) badges.push("English translation");
  if (item.signed_copy_required) badges.push("Signed copy");
  if (item.original_required) badges.push("Original required");
  if (item.copy_only) badges.push("Copy only");
  return badges;
}

export function ClientPortalChecklistPanel({
  checklist,
}: ClientPortalChecklistPanelProps): JSX.Element {
  const orderedItems = [...checklist.items].sort((left, right) => left.display_order - right.display_order);

  return (
    <Card
      title="Document Checklist"
      subtitle={`Progress ${checklist.progress.percent_complete}% · ${checklist.progress.received_items}/${checklist.progress.applicable_items} received`}
    >
      {!orderedItems.length ? (
        <EmptyState
          title="No checklist published"
          description="Your legal team has not added document requirements for this case yet."
        />
      ) : (
        <div className="page-stack">
          <div className="checklist-progress">
            <div className="checklist-progress__bar">
              <div
                className="checklist-progress__fill"
                style={{ width: `${checklist.progress.percent_complete}%` }}
              />
            </div>
            <div className="case-hero__badges">
              <Badge tone="neutral">{checklist.progress.total_items} total</Badge>
              <Badge tone="info">{checklist.progress.requested_items} requested</Badge>
              <Badge tone="warning">{checklist.progress.received_items} received</Badge>
              <Badge tone="success">{checklist.progress.validated_items} validated</Badge>
            </div>
          </div>

          <div className="checklist-items">
            {orderedItems.map((item) => (
              <div key={item.id} className="entity-card">
                <div className="entity-card__header entity-card__header--spread">
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.document_type ?? "General supporting document"}</p>
                  </div>
                  <div className="case-hero__badges">
                    <Badge tone={item.applies ? "info" : "neutral"}>
                      {item.applies ? "Applies" : "Not applicable"}
                    </Badge>
                    <Badge tone={item.requested ? "info" : "neutral"}>
                      {item.requested ? "Requested" : "Not requested"}
                    </Badge>
                    <Badge tone={item.received ? "warning" : "neutral"}>
                      {item.received ? "Received" : "Pending"}
                    </Badge>
                    <Badge tone={item.validated ? "success" : "neutral"}>
                      {item.validated ? "Validated" : "Awaiting review"}
                    </Badge>
                  </div>
                </div>

                {requirementBadges(item).length ? (
                  <div className="case-hero__badges">
                    {requirementBadges(item).map((badge) => (
                      <Badge key={`${item.id}-${badge}`} tone="warning">
                        {badge}
                      </Badge>
                    ))}
                  </div>
                ) : null}

                {item.observations ? (
                  <div className="placeholder-note">
                    <strong>Notes</strong>
                    <p>{item.observations}</p>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
