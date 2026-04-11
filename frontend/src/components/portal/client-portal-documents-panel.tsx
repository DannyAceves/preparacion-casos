"use client";

import { FormEvent, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import {
  isRocI751CaseType,
  localizeDocumentStatus,
  localizeProcessingStatus,
  localizeRocDocumentLabel,
  localizeRocDocumentType,
} from "@/lib/roc-i751-localization";
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
  const isRocChecklist = isRocI751CaseType(checklist.template_case_type);

  const selectedItem =
    applicableItems.find((item) => item.id === selectedChecklistItemId) ?? null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedFile) {
      setError("Selecciona un archivo para cargar.");
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
      setMessage("Documento cargado correctamente.");
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "No se pudo cargar el documento."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page-stack">
      <Card title="Cargar documentos" subtitle="Envia de forma segura los archivos solicitados a tu equipo legal.">
        <form className="entity-form" onSubmit={(event) => void handleSubmit(event)}>
          <div className="entity-form__grid">
            <FormField
              label="Documento solicitado"
              htmlFor="portal-checklist-item"
              hint="Elige el requisito correspondiente para que la lista del caso se actualice automaticamente."
            >
              <select
                id="portal-checklist-item"
                value={selectedChecklistItemId}
                onChange={(event) => setSelectedChecklistItemId(event.target.value)}
              >
                <option value="">Selecciona un requisito</option>
                {applicableItems.map((item) => (
                  <option key={item.id} value={item.id}>
                    {isRocChecklist ? localizeRocDocumentLabel(item.document_type, item.label) : item.label}
                  </option>
                ))}
              </select>
            </FormField>

            <FormField
              label="Tipo de documento"
              htmlFor="portal-document-type"
              hint="Usa este campo solo si el archivo no corresponde claramente a un requisito de la lista."
            >
              <input
                id="portal-document-type"
                value={
                  selectedItem?.document_type
                    ? (isRocChecklist
                        ? localizeRocDocumentType(selectedItem.document_type)
                        : selectedItem.document_type)
                    : manualDocumentType
                }
                disabled={Boolean(selectedItem?.document_type)}
                onChange={(event) => setManualDocumentType(event.target.value)}
                placeholder="acta_matrimonio, estados_bancarios, evidencia_relacion"
              />
            </FormField>

            <FormField label="Archivo" htmlFor="portal-document-file">
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
              {submitting ? "Cargando..." : "Cargar documento"}
            </button>
          </div>
        </form>
      </Card>

      <Card title="Documentos recibidos" subtitle="Archivos ya enviados por portal o capturados en el expediente.">
        <p className="entity-card__hint">Aqui solo se muestran los documentos asociados a este expediente.</p>
        {!documents.length ? (
          <EmptyState
            title="Aun no hay documentos recibidos"
            description="Carga el primer archivo para comenzar a integrar el expediente."
          />
        ) : (
          <div className="page-stack">
            {documents.map((document) => (
              <div key={document.id} className="entity-card">
                <div className="entity-card__header entity-card__header--spread">
                  <div>
                    <strong>{document.original_filename}</strong>
                    <p>
                      {isRocChecklist
                        ? localizeRocDocumentType(document.classification_label ?? document.document_type)
                        : document.classification_label ?? document.document_type}
                    </p>
                  </div>
                  <div className="case-hero__badges">
                    <Badge tone="warning">{localizeDocumentStatus(document.document_status)}</Badge>
                    <Badge tone="neutral">{document.mime_type}</Badge>
                  </div>
                </div>
                <div className="entity-card__grid">
                  <div>
                    <strong>Cargado</strong>
                    <p>{formatDateTime(document.uploaded_at)}</p>
                  </div>
                  <div>
                    <strong>Procesamiento</strong>
                    <p>{localizeProcessingStatus(document.processing_status)}</p>
                  </div>
                  <div>
                    <strong>Tamano</strong>
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
