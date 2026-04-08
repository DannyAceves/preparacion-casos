"use client";

import { FormEvent, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import { uploadClientPortalDocument } from "@/services/client-portal";
import { CaseDocumentChecklist, DocumentRecord } from "@/types/workspace";

interface ClientPortalDocumentsPanelProps {
  portalSessionToken: string;
  checklist: CaseDocumentChecklist;
  documents: DocumentRecord[];
  onRefresh: () => Promise<void>;
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

export function ClientPortalDocumentsPanel({
  portalSessionToken,
  checklist,
  documents,
  onRefresh,
}: ClientPortalDocumentsPanelProps): JSX.Element {
  const [selectedChecklistItemId, setSelectedChecklistItemId] = useState("");
  const [manualDocumentType, setManualDocumentType] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const applicableItems = useMemo(
    () => checklist.items.filter((item) => item.applies).sort((left, right) => left.display_order - right.display_order),
    [checklist.items],
  );

  const selectedItem =
    applicableItems.find((item) => item.id === selectedChecklistItemId) ?? null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedFile) {
      setError("Select a file to upload.");
      return;
    }

    setSubmitting(true);
    setMessage(null);
    setError(null);

    try {
      await uploadClientPortalDocument({
        portalSessionToken,
        file: selectedFile,
        checklistItemId: selectedItem?.id ?? null,
        documentType: selectedItem?.document_type ?? (manualDocumentType.trim() || null),
      });
      await onRefresh();
      setSelectedFile(null);
      setSelectedChecklistItemId("");
      setManualDocumentType("");
      setMessage("Document uploaded successfully.");
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "Could not upload document."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-stack">
      <Card title="Upload Documents" subtitle="Securely send the requested files to your legal team.">
        <form className="entity-form" onSubmit={(event) => void handleSubmit(event)}>
          <div className="entity-form__grid">
            <FormField
              label="Checklist item"
              htmlFor="portal-checklist-item"
              hint="Choose a requested item when possible so the case checklist updates automatically."
            >
              <select
                id="portal-checklist-item"
                value={selectedChecklistItemId}
                onChange={(event) => setSelectedChecklistItemId(event.target.value)}
              >
                <option value="">Select a document request</option>
                {applicableItems.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField
              label="Document type"
              htmlFor="portal-document-type"
              hint="Use this only if the file does not map cleanly to a checklist item."
            >
              <input
                id="portal-document-type"
                value={selectedItem?.document_type ?? manualDocumentType}
                disabled={Boolean(selectedItem?.document_type)}
                onChange={(event) => setManualDocumentType(event.target.value)}
                placeholder="passport, tax_return, marriage_certificate"
              />
            </FormField>

            <FormField label="File" htmlFor="portal-document-file">
              <input
                id="portal-document-file"
                type="file"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </FormField>
          </div>

          {message ? <FormFeedback tone="success" message={message} /> : null}
          {error ? <FormFeedback tone="error" message={error} /> : null}

          <div className="entity-form__actions">
            <button type="submit" className="ui-button" disabled={submitting}>
              {submitting ? "Uploading..." : "Upload document"}
            </button>
          </div>
        </form>
      </Card>

      <Card title="Received Documents" subtitle="Files already submitted through the portal or internal intake.">
        <p className="entity-card__hint">Only documents submitted through your own portal access are shown here.</p>
        {!documents.length ? (
          <EmptyState
            title="No documents received yet"
            description="Upload the first file to start building the case packet."
          />
        ) : (
          <div className="page-stack">
            {documents.map((document) => (
              <div key={document.id} className="entity-card">
                <div className="entity-card__header entity-card__header--spread">
                  <div>
                    <strong>{document.original_filename}</strong>
                    <p>{document.classification_label ?? document.document_type}</p>
                  </div>
                  <div className="case-hero__badges">
                    <Badge tone="warning">{document.document_status}</Badge>
                    <Badge tone="neutral">{document.mime_type}</Badge>
                  </div>
                </div>
                <div className="entity-card__grid">
                  <div>
                    <strong>Uploaded</strong>
                    <p>{formatDateTime(document.uploaded_at)}</p>
                  </div>
                  <div>
                    <strong>Status</strong>
                    <p>{document.processing_status}</p>
                  </div>
                  <div>
                    <strong>Size</strong>
                    <p>{Math.max(1, Math.round(document.size_bytes / 1024))} KB</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
