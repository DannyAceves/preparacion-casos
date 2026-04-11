import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { isRocI751CaseType, localizeRocDocumentLabel, localizeRocDocumentType } from "@/lib/roc-i751-localization";
import { CaseDocumentChecklist, CaseDocumentChecklistItem } from "@/types/workspace";

interface ClientPortalChecklistPanelProps {
  checklist: CaseDocumentChecklist;
}

function requirementBadges(item: CaseDocumentChecklistItem): string[] {
  const badges: string[] = [];
  if (item.color_required) badges.push("Color");
  if (item.english_translation_required) badges.push("Traduccion al ingles");
  if (item.signed_copy_required) badges.push("Con firma");
  if (item.original_required) badges.push("Original");
  if (item.copy_only) badges.push("Solo copia");
  return badges;
}

export function ClientPortalChecklistPanel({
  checklist,
}: ClientPortalChecklistPanelProps): JSX.Element {
  const orderedItems = [...checklist.items].sort((left, right) => left.display_order - right.display_order);
  const isRocChecklist = isRocI751CaseType(checklist.template_case_type);

  return (
    <Card
      title="Lista de documentos"
      subtitle={`Avance ${checklist.progress.percent_complete}% · ${checklist.progress.received_items}/${checklist.progress.applicable_items} recibidos`}
    >
      {!orderedItems.length ? (
        <EmptyState
          title="No hay lista publicada"
          description="Tu equipo legal todavia no ha agregado requisitos documentales para este caso."
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
              <Badge tone="info">{checklist.progress.requested_items} solicitados</Badge>
              <Badge tone="warning">{checklist.progress.received_items} recibidos</Badge>
              <Badge tone="success">{checklist.progress.validated_items} validados</Badge>
            </div>
          </div>

          <div className="checklist-items">
            {orderedItems.map((item) => (
              <div key={item.id} className="entity-card client-checklist-card">
                <div className="entity-card__header client-checklist-card__header">
                  <div>
                    <strong>{isRocChecklist ? localizeRocDocumentLabel(item.document_type, item.label) : item.label}</strong>
                    <p>{isRocChecklist ? localizeRocDocumentType(item.document_type) : item.document_type ?? "Documento general de soporte"}</p>
                  </div>
                  <div className="case-hero__badges client-checklist-card__badges">
                    <Badge tone={item.applies ? "info" : "neutral"}>
                      {item.applies ? "Aplica" : "No aplica"}
                    </Badge>
                    <Badge tone={item.requested ? "info" : "neutral"}>
                      {item.requested ? "Solicitado" : "No solicitado"}
                    </Badge>
                    <Badge tone={item.received ? "warning" : "neutral"}>
                      {item.received ? "Recibido" : "Pendiente"}
                    </Badge>
                    <Badge tone={item.validated ? "success" : "neutral"}>
                      {item.validated ? "Validado" : "Pendiente de revision"}
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
                    <strong>Notas</strong>
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
