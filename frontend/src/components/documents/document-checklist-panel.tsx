"use client";

import { FormEvent, useMemo, useState } from "react";

import {
  addCaseDocumentChecklistItem,
  reorderCaseDocumentChecklistItems,
  syncCaseDocumentChecklist,
  updateCaseDocumentChecklistItem,
} from "@/services/document-checklist";
import { Card } from "@/components/ui/card";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { getApiErrorMessage } from "@/lib/api/errors";
import { usePermissions } from "@/hooks/use-permissions";
import { CaseDocumentChecklist, CaseDocumentChecklistItem } from "@/types/workspace";

interface DocumentChecklistPanelProps {
  caseId: string;
  checklist: CaseDocumentChecklist;
  onRefresh: () => Promise<void>;
}

interface ManualItemState {
  label: string;
  documentType: string;
  observations: string;
  colorRequired: boolean;
  englishTranslationRequired: boolean;
  signedCopyRequired: boolean;
  originalRequired: boolean;
  copyOnly: boolean;
}

const initialManualItemState: ManualItemState = {
  label: "",
  documentType: "",
  observations: "",
  colorRequired: false,
  englishTranslationRequired: false,
  signedCopyRequired: false,
  originalRequired: false,
  copyOnly: false,
};

function requirementBadges(item: CaseDocumentChecklistItem): string[] {
  const badges: string[] = [];
  if (item.color_required) badges.push("Color required");
  if (item.english_translation_required) badges.push("English translation");
  if (item.signed_copy_required) badges.push("Signed copy");
  if (item.original_required) badges.push("Original required");
  if (item.copy_only) badges.push("Copy only");
  return badges;
}

export function DocumentChecklistPanel({
  caseId,
  checklist,
  onRefresh,
}: DocumentChecklistPanelProps): JSX.Element {
  const permissions = usePermissions();
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"save" | "reorder" | "sync" | "create" | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [manualItem, setManualItem] = useState<ManualItemState>(initialManualItemState);
  const orderedItems = useMemo(
    () => [...checklist.items].sort((left, right) => left.display_order - right.display_order),
    [checklist.items],
  );

  async function handleUpdate(
    itemId: string,
    payload: Parameters<typeof updateCaseDocumentChecklistItem>[0],
    successMessage: string,
  ): Promise<void> {
    setBusyItemId(itemId);
    setBusyAction("save");
    setPanelMessage(null);
    setPanelError(null);
    try {
      await updateCaseDocumentChecklistItem(payload);
      await onRefresh();
      setPanelMessage(successMessage);
    } catch (error) {
      setPanelError(getApiErrorMessage(error, "Could not update checklist item."));
    } finally {
      setBusyItemId(null);
      setBusyAction(null);
    }
  }

  async function handleMove(itemId: string, direction: -1 | 1): Promise<void> {
    const index = orderedItems.findIndex((item) => item.id === itemId);
    if (index < 0) {
      return;
    }
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= orderedItems.length) {
      return;
    }

    const nextIds = orderedItems.map((item) => item.id);
    const [moved] = nextIds.splice(index, 1);
    nextIds.splice(targetIndex, 0, moved);

    setBusyItemId(itemId);
    setBusyAction("reorder");
    setPanelMessage(null);
    setPanelError(null);
    try {
      await reorderCaseDocumentChecklistItems(caseId, nextIds);
      await onRefresh();
      setPanelMessage("Checklist order updated.");
    } catch (error) {
      setPanelError(getApiErrorMessage(error, "Could not reorder checklist items."));
    } finally {
      setBusyItemId(null);
      setBusyAction(null);
    }
  }

  async function handleSyncTemplate(): Promise<void> {
    setBusyAction("sync");
    setPanelMessage(null);
    setPanelError(null);
    try {
      await syncCaseDocumentChecklist(caseId);
      await onRefresh();
      setPanelMessage("Checklist template synced successfully.");
    } catch (error) {
      setPanelError(getApiErrorMessage(error, "Could not sync checklist template."));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleAddManualItem(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setBusyAction("create");
    setPanelMessage(null);
    setPanelError(null);
    try {
      await addCaseDocumentChecklistItem({
        caseId,
        label: manualItem.label.trim(),
        documentType: manualItem.documentType.trim() || null,
        observations: manualItem.observations.trim() || null,
        colorRequired: manualItem.colorRequired,
        englishTranslationRequired: manualItem.englishTranslationRequired,
        signedCopyRequired: manualItem.signedCopyRequired,
        originalRequired: manualItem.originalRequired,
        copyOnly: manualItem.copyOnly,
      });
      await onRefresh();
      setManualItem(initialManualItemState);
      setPanelMessage("Manual checklist item added.");
    } catch (error) {
      setPanelError(getApiErrorMessage(error, "Could not add checklist item."));
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <div className="detail-sections">
      <Card
        title="Document Checklist"
        subtitle={`Progress ${checklist.progress.percent_complete}% · ${checklist.progress.validated_items}/${checklist.progress.applicable_items} validated`}
      >
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

          <div className="case-quick-actions">
            <button
              type="button"
              className="ui-button ui-button--ghost"
              disabled={busyAction === "sync" || !permissions.can("manage_documents")}
              onClick={() => void handleSyncTemplate()}
            >
              {busyAction === "sync"
                ? "Syncing..."
                : permissions.can("manage_documents")
                  ? "Sync Template Items"
                  : "Checklist Sync Restricted"}
            </button>
          </div>

          {panelMessage ? <FormFeedback tone="success" message={panelMessage} /> : null}
          {panelError ? <FormFeedback tone="error" message={panelError} /> : null}

          {!orderedItems.length ? (
            <EmptyState
              title="No checklist items"
              description="The system could not derive template items for this case type yet."
            />
          ) : (
            <div className="checklist-items">
              {orderedItems.map((item, index) => {
                const attrs = requirementBadges(item);
                return (
                  <div key={item.id} className="entity-card">
                    <div className="entity-card__header entity-card__header--spread">
                      <div>
                        <strong>{item.label}</strong>
                        <p>
                          {item.document_type ?? "manual item"} | {item.linked_document_count} linked document
                          {item.linked_document_count === 1 ? "" : "s"}
                        </p>
                      </div>
                      <div className="case-hero__badges">
                        <Badge tone={item.applies ? "info" : "neutral"}>
                          {item.applies ? "applies" : "not applicable"}
                        </Badge>
                        {item.is_manual ? <Badge tone="warning">manual</Badge> : null}
                      </div>
                    </div>

                    <div className="checklist-item__toggles">
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.applies}
                          disabled={busyItemId === item.id || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, applies: event.target.checked },
                              "Checklist applicability updated.",
                            )
                          }
                        />
                        <span>Applies</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.requested}
                          disabled={busyItemId === item.id || !item.applies || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, requested: event.target.checked },
                              "Checklist requested state updated.",
                            )
                          }
                        />
                        <span>Requested</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.received}
                          disabled={busyItemId === item.id || !item.applies || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, received: event.target.checked },
                              "Checklist received state updated.",
                            )
                          }
                        />
                        <span>Received</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.validated}
                          disabled={busyItemId === item.id || !item.applies || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, validated: event.target.checked },
                              "Checklist validated state updated.",
                            )
                          }
                        />
                        <span>Validated</span>
                      </label>
                    </div>

                    {attrs.length ? (
                      <div className="case-hero__badges">
                        {attrs.map((attribute) => (
                          <Badge key={attribute} tone="neutral">
                            {attribute}
                          </Badge>
                        ))}
                      </div>
                    ) : null}

                    <div className="checklist-item__toggles">
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.color_required}
                          disabled={busyItemId === item.id || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, colorRequired: event.target.checked },
                              "Checklist item requirements updated.",
                            )
                          }
                        />
                        <span>Color required</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.english_translation_required}
                          disabled={busyItemId === item.id || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              {
                                caseId,
                                itemId: item.id,
                                englishTranslationRequired: event.target.checked,
                              },
                              "Checklist item requirements updated.",
                            )
                          }
                        />
                        <span>English translation</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.signed_copy_required}
                          disabled={busyItemId === item.id || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, signedCopyRequired: event.target.checked },
                              "Checklist item requirements updated.",
                            )
                          }
                        />
                        <span>Signed copy</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.original_required}
                          disabled={busyItemId === item.id || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, originalRequired: event.target.checked },
                              "Checklist item requirements updated.",
                            )
                          }
                        />
                        <span>Original required</span>
                      </label>
                      <label className="checklist-toggle">
                        <input
                          type="checkbox"
                          checked={item.copy_only}
                          disabled={busyItemId === item.id || !permissions.can("manage_documents")}
                          onChange={(event) =>
                            void handleUpdate(
                              item.id,
                              { caseId, itemId: item.id, copyOnly: event.target.checked },
                              "Checklist item requirements updated.",
                            )
                          }
                        />
                        <span>Copy only</span>
                      </label>
                    </div>

                    <label className="ui-field">
                      <span>Observations</span>
                      <textarea
                        key={`${item.id}-${item.updated_at}`}
                        className="ui-textarea"
                        rows={3}
                        defaultValue={item.observations ?? ""}
                        disabled={!permissions.can("manage_documents")}
                        onBlur={(event) => {
                          if ((item.observations ?? "") === event.target.value) {
                            return;
                          }
                          void handleUpdate(
                            item.id,
                            { caseId, itemId: item.id, observations: event.target.value || null },
                            "Checklist observations updated.",
                          );
                        }}
                      />
                    </label>

                    <div className="case-quick-actions">
                      <button
                        type="button"
                        className="ui-button ui-button--ghost"
                        disabled={busyAction === "reorder" || index === 0 || !permissions.can("manage_documents")}
                        onClick={() => void handleMove(item.id, -1)}
                      >
                        Move Up
                      </button>
                      <button
                        type="button"
                        className="ui-button ui-button--ghost"
                        disabled={
                          busyAction === "reorder" || index === orderedItems.length - 1 || !permissions.can("manage_documents")
                        }
                        onClick={() => void handleMove(item.id, 1)}
                      >
                        Move Down
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Card>

      <Card title="Add Manual Checklist Item" subtitle="Capture interview-specific evidence requirements not covered by the base template.">
        <form className="entity-form" onSubmit={handleAddManualItem}>
          <div className="entity-form__grid">
            <FormField label="Label" htmlFor="manual-checklist-label">
              <input
                id="manual-checklist-label"
                value={manualItem.label}
                onChange={(event) => setManualItem((current) => ({ ...current, label: event.target.value }))}
                disabled={busyAction === "create" || !permissions.can("manage_documents")}
              />
            </FormField>
            <FormField label="Document type" htmlFor="manual-checklist-document-type">
              <input
                id="manual-checklist-document-type"
                value={manualItem.documentType}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, documentType: event.target.value }))
                }
                disabled={busyAction === "create" || !permissions.can("manage_documents")}
                placeholder="supporting-affidavit"
              />
            </FormField>
            <FormField label="Observations" htmlFor="manual-checklist-observations">
              <textarea
                id="manual-checklist-observations"
                className="ui-textarea"
                rows={3}
                value={manualItem.observations}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, observations: event.target.value }))
                }
                disabled={busyAction === "create" || !permissions.can("manage_documents")}
              />
            </FormField>
          </div>

          <div className="checklist-item__toggles">
            <label className="checklist-toggle">
              <input
                type="checkbox"
                checked={manualItem.colorRequired}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, colorRequired: event.target.checked }))
                }
                disabled={!permissions.can("manage_documents")}
              />
              <span>Color required</span>
            </label>
            <label className="checklist-toggle">
              <input
                type="checkbox"
                checked={manualItem.englishTranslationRequired}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, englishTranslationRequired: event.target.checked }))
                }
                disabled={!permissions.can("manage_documents")}
              />
              <span>English translation required</span>
            </label>
            <label className="checklist-toggle">
              <input
                type="checkbox"
                checked={manualItem.signedCopyRequired}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, signedCopyRequired: event.target.checked }))
                }
                disabled={!permissions.can("manage_documents")}
              />
              <span>Signed copy required</span>
            </label>
            <label className="checklist-toggle">
              <input
                type="checkbox"
                checked={manualItem.originalRequired}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, originalRequired: event.target.checked }))
                }
                disabled={!permissions.can("manage_documents")}
              />
              <span>Original required</span>
            </label>
            <label className="checklist-toggle">
              <input
                type="checkbox"
                checked={manualItem.copyOnly}
                onChange={(event) =>
                  setManualItem((current) => ({ ...current, copyOnly: event.target.checked }))
                }
                disabled={!permissions.can("manage_documents")}
              />
              <span>Copy only</span>
            </label>
          </div>

          <div className="entity-form__actions">
            <button
              type="submit"
              className="ui-button"
              disabled={busyAction === "create" || !manualItem.label.trim() || !permissions.can("manage_documents")}
            >
              {permissions.can("manage_documents")
                ? busyAction === "create"
                  ? "Adding..."
                  : "Add Checklist Item"
                : "Checklist Editing Restricted"}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
}
