"use client";

import { useState } from "react";

import { DocumentChecklistPanel } from "@/components/documents/document-checklist-panel";
import { DocumentUploader } from "@/components/documents/document-uploader";
import { DocumentsTable } from "@/components/documents/documents-table";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { reprocessDocument, replaceDocument, uploadCaseDocument } from "@/services/documents";
import { ApiErrorPayload } from "@/types/api";
import { CaseDocumentChecklist, DocumentRecord } from "@/types/workspace";

interface CaseDocumentsPanelProps {
  caseId: string;
  documents: DocumentRecord[];
  checklist: CaseDocumentChecklist;
  loading: boolean;
  error: ApiErrorPayload | null;
  onRefresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Document action failed.";
}

export function CaseDocumentsPanel({
  caseId,
  documents,
  checklist,
  loading,
  error,
  onRefresh,
}: CaseDocumentsPanelProps): JSX.Element {
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null);
  const currentDocuments = documents.filter((document) => document.is_current);

  async function handleUpload(input: {
    uploadedByUserId: string;
    file: File;
    documentStatus?: string;
    classificationLabel?: string;
    classificationSource?: string;
  }): Promise<void> {
    setActionMessage(null);
    setActionError(null);

    try {
      await uploadCaseDocument({
        caseId,
        uploadedByUserId: input.uploadedByUserId,
        file: input.file,
        documentStatus: input.documentStatus,
        classificationLabel: input.classificationLabel,
        classificationSource: input.classificationSource,
      });
      await onRefresh();
      setActionMessage("Document uploaded successfully.");
    } catch (uploadError) {
      setActionError(getErrorMessage(uploadError));
      throw uploadError;
    }
  }

  async function handleReplace(
    documentId: string,
    input: {
      uploadedByUserId: string;
      file: File;
      documentStatus?: string;
      replacementNotes?: string;
    },
  ): Promise<void> {
    setBusyDocumentId(documentId);
    setActionMessage(null);
    setActionError(null);

    try {
      await replaceDocument({
        documentId,
        uploadedByUserId: input.uploadedByUserId,
        file: input.file,
        documentStatus: input.documentStatus,
        replacementNotes: input.replacementNotes,
      });
      await onRefresh();
      setActionMessage("Document replacement uploaded successfully.");
    } catch (replaceError) {
      setActionError(getErrorMessage(replaceError));
      throw replaceError;
    } finally {
      setBusyDocumentId(null);
    }
  }

  async function handleReprocess(documentId: string, actorReference: string): Promise<void> {
    setBusyDocumentId(documentId);
    setActionMessage(null);
    setActionError(null);

    try {
      await reprocessDocument({ documentId, actorReference });
      await onRefresh();
      setActionMessage("Document reprocessing queued.");
    } catch (reprocessError) {
      setActionError(getErrorMessage(reprocessError));
    } finally {
      setBusyDocumentId(null);
    }
  }

  return (
    <div className="detail-sections">
      <DocumentChecklistPanel caseId={caseId} checklist={checklist} onRefresh={onRefresh} />

      <Card title="Upload Document" subtitle="Attach a new document to this case">
        <DocumentUploader
          title="New document"
          actionLabel="Upload document"
          busyLabel="Uploading document..."
          allowClassification
          onSubmit={handleUpload}
        />
      </Card>

      <Card title="Documents" subtitle="Current versions available for review and processing">
        {loading ? <LoadingState label="Loading case documents..." /> : null}
        {!loading && error ? (
          <ErrorState title="Could not load documents" description="The document section could not be retrieved from the backend." />
        ) : null}
        {!loading && !error && !currentDocuments.length ? (
          <EmptyState
            title="No documents uploaded"
            description="Upload the first document for this case to start document processing and review."
          />
        ) : null}
        {!loading && !error && currentDocuments.length ? (
          <DocumentsTable
            documents={currentDocuments}
            actionMessage={actionMessage}
            actionError={actionError}
            busyDocumentId={busyDocumentId}
            onReplace={handleReplace}
            onReprocess={handleReprocess}
          />
        ) : null}
      </Card>
    </div>
  );
}
