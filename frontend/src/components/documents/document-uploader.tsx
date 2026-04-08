"use client";

import { FormEvent, useState } from "react";

import { usePermissions } from "@/hooks/use-permissions";

interface DocumentUploaderProps {
  title: string;
  actionLabel: string;
  busyLabel: string;
  onSubmit: (input: {
    uploadedByUserId: string;
    file: File;
    documentStatus?: string;
    classificationLabel?: string;
    classificationSource?: string;
    replacementNotes?: string;
  }) => Promise<void>;
  allowClassification?: boolean;
  allowReplacementNotes?: boolean;
}

export function DocumentUploader({
  title,
  actionLabel,
  busyLabel,
  onSubmit,
  allowClassification = false,
  allowReplacementNotes = false,
}: DocumentUploaderProps): JSX.Element {
  const permissions = usePermissions();
  const [uploadedByUserId, setUploadedByUserId] = useState("");
  const [documentStatus, setDocumentStatus] = useState("uploaded");
  const [classificationLabel, setClassificationLabel] = useState("");
  const [classificationSource, setClassificationSource] = useState("");
  const [replacementNotes, setReplacementNotes] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!file || !uploadedByUserId.trim()) {
      setLocalError("Uploader user and file are required.");
      return;
    }

    setSubmitting(true);
    setLocalError(null);

    try {
      await onSubmit({
        uploadedByUserId: uploadedByUserId.trim(),
        file,
        documentStatus: documentStatus.trim() || undefined,
        classificationLabel: classificationLabel.trim() || undefined,
        classificationSource: classificationSource.trim() || undefined,
        replacementNotes: replacementNotes.trim() || undefined,
      });
      setFile(null);
      setDocumentStatus("uploaded");
      setClassificationLabel("");
      setClassificationSource("");
      setReplacementNotes("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Document action failed.";
      setLocalError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="document-uploader" onSubmit={(event) => void handleSubmit(event)}>
      <div className="document-uploader__header">
        <strong>{title}</strong>
        <span>Allowed types and limits are enforced by the backend.</span>
      </div>

      <div className="document-uploader__grid">
        <label className="ui-field">
          <span>Uploaded By User</span>
          <input
            value={uploadedByUserId}
            onChange={(event) => setUploadedByUserId(event.target.value)}
            placeholder="staff.user"
            disabled={!permissions.can("manage_documents")}
          />
        </label>

        <label className="ui-field">
          <span>Document Status</span>
          <input
            value={documentStatus}
            onChange={(event) => setDocumentStatus(event.target.value)}
            placeholder="uploaded"
            disabled={!permissions.can("manage_documents")}
          />
        </label>

        <label className="ui-field document-uploader__file">
          <span>File</span>
          <input type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} disabled={!permissions.can("manage_documents")} />
        </label>

        {allowClassification ? (
          <>
            <label className="ui-field">
              <span>Classification Label</span>
              <input
                value={classificationLabel}
                onChange={(event) => setClassificationLabel(event.target.value)}
                placeholder="passport"
                disabled={!permissions.can("manage_documents")}
              />
            </label>

            <label className="ui-field">
              <span>Classification Source</span>
              <input
                value={classificationSource}
                onChange={(event) => setClassificationSource(event.target.value)}
                placeholder="manual"
                disabled={!permissions.can("manage_documents")}
              />
            </label>
          </>
        ) : null}

        {allowReplacementNotes ? (
          <label className="ui-field document-uploader__notes">
            <span>Replacement Notes</span>
            <input
              value={replacementNotes}
              onChange={(event) => setReplacementNotes(event.target.value)}
              placeholder="Why this version replaces the previous file"
              disabled={!permissions.can("manage_documents")}
            />
          </label>
        ) : null}
      </div>

      {localError ? <p className="document-feedback document-feedback--error">{localError}</p> : null}

      <button type="submit" className="ui-button" disabled={submitting || !permissions.can("manage_documents")}>
        {permissions.can("manage_documents") ? (submitting ? busyLabel : actionLabel) : "Upload Restricted"}
      </button>
    </form>
  );
}
