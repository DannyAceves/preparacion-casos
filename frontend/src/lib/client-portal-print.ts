import { ClientPortalContext } from "@/types/client-portal";
import { QuestionnaireQuestion } from "@/types/workspace";
import {
  isRocI751CaseType,
  localizeRocDocumentLabel,
  localizeRocDocumentType,
  localizeRocQuestion,
  localizeRocRepeatableField,
  localizeRocSection,
} from "@/lib/roc-i751-localization";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "No disponible";
  }
  return new Date(value).toLocaleString();
}

function formatQuestionValue(question: QuestionnaireQuestion): string {
  const answer = question.answer;
  if (!answer) {
    return "Sin respuesta";
  }

  if (answer.answer_text) {
    return answer.answer_text;
  }
  if (answer.answer_date) {
    return answer.answer_date;
  }
  if (answer.answer_boolean !== null) {
    return answer.answer_boolean ? "Si" : "No";
  }
  if (answer.answer_choice) {
    const option = (question.options ?? []).find((item) => item.value === answer.answer_choice);
    return option?.label ?? answer.answer_choice;
  }
  if (answer.answer_choices?.length) {
    return answer.answer_choices.join(", ");
  }
  if (Array.isArray(answer.answer_json)) {
    return answer.answer_json
      .map((item, index) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) {
          return `Registro ${index + 1}: ${String(item)}`;
        }
        return [
          `Registro ${index + 1}`,
          ...Object.entries(item).map(([key, value]) => `${localizeRocRepeatableField(key)}: ${value ?? ""}`),
        ].join("\n");
      })
      .join("\n\n");
  }
  if (answer.answer_json && typeof answer.answer_json === "object") {
    return Object.entries(answer.answer_json)
      .map(([key, value]) => `${localizeRocRepeatableField(key)}: ${value ?? ""}`)
      .join("\n");
  }
  return "Sin respuesta";
}

function buildPrintableHtml(context: ClientPortalContext): string {
  const isRocCase = isRocI751CaseType(context.case_type);
  const questionnaireSections = (context.questionnaire?.sections ?? [])
    .map((section) => {
      const localizedSection = isRocCase
        ? localizeRocSection(section.title, section.description)
        : { title: section.title, description: section.description ?? null };
      const questions = section.questions
        .map((question) => {
          const localizedQuestion = isRocCase ? localizeRocQuestion(question) : question;
          return `
            <div class="question-row">
              <div class="question-meta">
                <div class="question-label">${escapeHtml(localizedQuestion.prompt)}</div>
                <div class="question-required">${localizedQuestion.is_required ? "Obligatoria" : "Opcional"}</div>
              </div>
              <pre class="question-answer">${escapeHtml(formatQuestionValue(localizedQuestion))}</pre>
            </div>
          `;
        })
        .join("");
      return `
        <section class="print-section">
          <h2>${escapeHtml(localizedSection.title)}</h2>
          ${localizedSection.description ? `<p class="section-description">${escapeHtml(localizedSection.description)}</p>` : ""}
          <div class="question-list">${questions}</div>
        </section>
      `;
    })
    .join("");

  const checklistRows = context.checklist.items
    .filter((item) => item.applies)
    .sort((left, right) => left.display_order - right.display_order)
    .map((item) => {
      const label = isRocCase ? localizeRocDocumentLabel(item.document_type, item.label) : item.label;
      const typeLabel = isRocCase ? localizeRocDocumentType(item.document_type) : item.document_type ?? "Documento";
      const status = item.validated ? "Validado" : item.received ? "Recibido" : item.requested ? "Pendiente" : "Informativo";
      return `
        <tr>
          <td>${escapeHtml(label)}</td>
          <td>${escapeHtml(typeLabel)}</td>
          <td>${escapeHtml(status)}</td>
          <td>${item.observations ? escapeHtml(item.observations) : "Sin notas"}</td>
        </tr>
      `;
    })
    .join("");

  return `<!doctype html>
  <html lang="es">
    <head>
      <meta charset="utf-8" />
      <title>${escapeHtml(context.case_number)} - Cuestionario del cliente</title>
      <style>
        body {
          margin: 0;
          padding: 32px;
          font-family: "Segoe UI", "Helvetica Neue", sans-serif;
          color: #17303d;
          background: #f3f7fa;
        }
        .sheet {
          max-width: 980px;
          margin: 0 auto;
          background: #fff;
          border: 1px solid #d9e1ea;
          border-radius: 20px;
          padding: 32px;
          box-shadow: 0 18px 45px rgba(15, 30, 45, 0.08);
        }
        .hero h1 {
          margin: 8px 0;
          font-size: 28px;
        }
        .hero p, .meta, .section-description {
          color: #5a6775;
        }
        .meta-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin: 20px 0 28px;
        }
        .meta-card {
          border: 1px solid #d9e1ea;
          border-radius: 14px;
          background: #f8fbfd;
          padding: 14px;
        }
        .meta-card strong {
          display: block;
          margin-bottom: 6px;
        }
        .print-section {
          margin-top: 28px;
          page-break-inside: avoid;
          break-inside: avoid;
        }
        .print-section h2 {
          margin: 0 0 10px;
          font-size: 20px;
        }
        .question-list {
          display: grid;
          gap: 12px;
        }
        .question-row {
          border: 1px solid #d9e1ea;
          border-radius: 14px;
          padding: 14px 16px;
          background: #fcfdfe;
          page-break-inside: avoid;
          break-inside: avoid;
          -webkit-column-break-inside: avoid;
        }
        .question-meta {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 10px;
        }
        .question-label {
          font-weight: 700;
        }
        .question-required {
          color: #5a6775;
          white-space: nowrap;
        }
        .question-answer {
          margin: 0;
          white-space: pre-wrap;
          font: inherit;
          color: #17303d;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 12px;
        }
        th, td {
          border-bottom: 1px solid #d9e1ea;
          padding: 10px 8px;
          text-align: left;
          vertical-align: top;
        }
        th {
          color: #5a6775;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        @media print {
          body {
            background: #fff;
            padding: 0;
          }
          .sheet {
            border: 0;
            box-shadow: none;
            border-radius: 0;
            max-width: none;
            padding: 18mm 14mm;
          }
          .question-list {
            display: block;
          }
          .question-row {
            display: block;
            margin-bottom: 12px;
            page-break-inside: avoid;
            break-inside: avoid-page;
          }
          .question-meta {
            display: flex;
            align-items: flex-start;
          }
        }
      </style>
    </head>
    <body>
      <div class="sheet">
        <header class="hero">
          <div class="meta">Portal del cliente · Cuestionario exportable</div>
          <h1>${escapeHtml(context.case_title)}</h1>
          <p>${escapeHtml(context.case_number)} · ${escapeHtml(context.case_type)}</p>
          <p>${escapeHtml(context.case_summary ?? "Resumen no disponible.")}</p>
        </header>

        <section class="meta-grid">
          <div class="meta-card">
            <strong>Progreso general</strong>
            <span>${context.progress.overall_percent_complete}% completado</span>
          </div>
          <div class="meta-card">
            <strong>Cuestionario</strong>
            <span>${context.progress.questionnaire_answered_questions}/${context.progress.questionnaire_total_questions} respuestas</span>
          </div>
          <div class="meta-card">
            <strong>Sesion vigente</strong>
            <span>${escapeHtml(formatDateTime(context.session_expires_at))}</span>
          </div>
        </section>

        ${context.instructions ? `<section class="print-section"><h2>Instrucciones</h2><p>${escapeHtml(context.instructions)}</p></section>` : ""}

        <section class="print-section">
          <h2>Lista de documentos</h2>
          <table>
            <thead>
              <tr>
                <th>Documento</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Notas</th>
              </tr>
            </thead>
            <tbody>
              ${checklistRows}
            </tbody>
          </table>
        </section>

        ${questionnaireSections || `<section class="print-section"><h2>Cuestionario</h2><p>No hay cuestionario disponible.</p></section>`}
      </div>
    </body>
  </html>`;
}

export function openClientPortalPrintablePdf(context: ClientPortalContext): void {
  const iframe = document.createElement("iframe");
  iframe.setAttribute("aria-hidden", "true");
  iframe.style.position = "fixed";
  iframe.style.right = "0";
  iframe.style.bottom = "0";
  iframe.style.width = "0";
  iframe.style.height = "0";
  iframe.style.border = "0";
  iframe.style.opacity = "0";
  iframe.style.pointerEvents = "none";

  const cleanup = (): void => {
    window.setTimeout(() => {
      iframe.remove();
    }, 250);
  };

  iframe.onload = () => {
    const frameWindow = iframe.contentWindow;
    if (!frameWindow) {
      cleanup();
      throw new Error("No se pudo preparar la impresion del PDF.");
    }

    frameWindow.focus();
    window.setTimeout(() => {
      frameWindow.print();
    }, 150);

    frameWindow.addEventListener("afterprint", cleanup, { once: true });
    window.setTimeout(cleanup, 2000);
  };

  document.body.appendChild(iframe);

  const printDocument = iframe.contentDocument;
  if (!printDocument) {
    cleanup();
    throw new Error("No se pudo abrir el documento de impresion.");
  }

  printDocument.open();
  printDocument.write(buildPrintableHtml(context));
  printDocument.close();
}
