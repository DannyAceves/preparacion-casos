"use client";

import { Fragment, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { DocumentUploader } from "@/components/documents/document-uploader";
import { usePermissions } from "@/hooks/use-permissions";
import { DocumentRecord } from "@/types/workspace";

interface DocumentsTableProps {
  documents: DocumentRecord[];
  actionMessage: string | null;
  actionError: string | null;
  busyDocumentId: string | null;
  onReplace: (documentId: string, input: { uploadedByUserId: string; file: File; documentStatus?: string; replacementNotes?: string }) => Promise<void>;
  onReprocess: (documentId: string, actorReference: string) => Promise<void>;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function toneForStatus(status: string): "neutral" | "success" | "warning" | "danger" | "info" {
  if (status === "approved" || status === "completed" || status === "submitted") {
    return "success";
  }
  if (status === "failed" || status === "manual_review_required" || status === "rejected") {
    return "danger";
  }
  if (status === "processing" || status === "queued" || status === "under_review") {
    return "warning";
  }
  return "info";
}

export function DocumentsTable({
  documents,
  actionMessage,
  actionError,
  busyDocumentId,
  onReplace,
  onReprocess,
}: DocumentsTableProps): JSX.Element {
  const permissions = usePermissions();
  const [expandedDocumentId, setExpandedDocumentId] = useState<string | null>(null);
  const [reprocessActor, setReprocessActor] = useState<Record<string, string>>({});

  return (
    <div className="page-stack">
      {actionMessage ? <p className="document-feedback document-feedback--success">{actionMessage}</p> : null}
      {actionError ? <p className="document-feedback document-feedback--error">{actionError}</p> : null}

      <div className="ui-table-wrap">
        <table className="ui-table">
          <thead>
            <tr>
              <th>File</th>
              <th>MIME Type</th>
              <th>Size</th>
              <th>Uploaded</th>
              <th>Document Status</th>
              <th>Processing</th>
              <th>Classification</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => {
              const isExpanded = expandedDocumentId === document.id;
              const actorValue = reprocessActor[document.id] ?? "";

              return (
                <Fragment key={document.id}>
                  <tr>
                    <td>
                      <div className="ui-table__primary">{document.original_filename}</div>
                      <div className="ui-table__secondary">v{document.version_number}</div>
                    </td>
                    <td>{document.mime_type}</td>
                    <td>{formatSize(document.size_bytes)}</td>
                    <td>{new Date(document.uploaded_at).toLocaleString()}</td>
                    <td>
                      <Badge tone={toneForStatus(document.document_status)}>{document.document_status}</Badge>
                    </td>
                    <td>
                      <Badge tone={toneForStatus(document.processing_status)}>{document.processing_status}</Badge>
                    </td>
                    <td>{document.classification_label ?? "Unclassified"}</td>
                    <td>
                      <div className="document-actions">
                        <button
                          type="button"
                          className="ui-button ui-button--ghost"
                          disabled={!permissions.can("manage_documents")}
                          onClick={() => setExpandedDocumentId(isExpanded ? null : document.id)}
                        >
                          {!permissions.can("manage_documents") ? "Replace Restricted" : isExpanded ? "Hide replace" : "Replace"}
                        </button>

                        <input
                          className="document-actions__actor"
                          value={actorValue}
                          onChange={(event) =>
                            setReprocessActor((current) => ({ ...current, [document.id]: event.target.value }))
                          }
                          placeholder="actor.user"
                          disabled={!permissions.can("manage_documents")}
                        />

                        <button
                          type="button"
                          className="ui-button"
                          disabled={busyDocumentId === document.id || !actorValue.trim() || !permissions.can("manage_documents")}
                          onClick={() => void onReprocess(document.id, actorValue.trim())}
                        >
                          {permissions.can("manage_documents")
                            ? busyDocumentId === document.id
                              ? "Reprocessing..."
                              : "Reprocess"
                            : "Reprocess Restricted"}
                        </button>
                      </div>
                    </td>
                  </tr>
                  {isExpanded ? (
                    <tr>
                      <td colSpan={8}>
                        <DocumentUploader
                          title={`Replace ${document.original_filename}`}
                          actionLabel="Upload replacement"
                          busyLabel="Uploading replacement..."
                          allowReplacementNotes
                          onSubmit={(input) =>
                            onReplace(document.id, {
                              uploadedByUserId: input.uploadedByUserId,
                              file: input.file,
                              documentStatus: input.documentStatus,
                              replacementNotes: input.replacementNotes,
                            })
                          }
                        />
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
