"use client";

import { startTransition, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { CanonicalFieldsPanel } from "@/components/canonical-fields/canonical-fields-panel";
import { CaseQuickActions } from "@/components/cases/case-quick-actions";
import { CaseDocumentsPanel } from "@/components/documents/case-documents-panel";
import { FormsPanel } from "@/components/forms/forms-panel";
import { InconsistenciesPanel } from "@/components/inconsistencies/inconsistencies-panel";
import { PacketPanel } from "@/components/packet/packet-panel";
import { ClientPortalAccessPanel } from "@/components/portal/client-portal-access-panel";
import { CaseQuestionnairePanel } from "@/components/questionnaire/case-questionnaire-panel";
import { ReadinessPanel } from "@/components/readiness/readiness-panel";
import { SubmissionPanel } from "@/components/submission/submission-panel";
import { TimelinePanel } from "@/components/timeline/timeline-panel";
import { usePermissions } from "@/hooks/use-permissions";
import { useCaseWorkspace } from "@/hooks/use-case-workspace";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { TabPanel, Tabs } from "@/components/ui/tabs";
import { Case, CaseReadiness } from "@/types/case";
import { CaseWorkspaceData } from "@/types/workspace";

type CaseWorkspaceTabKey =
  | "overview"
  | "questionnaire"
  | "documents"
  | "canonical-fields"
  | "inconsistencies"
  | "reviews"
  | "forms"
  | "packet"
  | "readiness"
  | "submission"
  | "timeline";

interface Case360TabsProps {
  caseItem: Case;
  readiness: CaseReadiness;
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

function toneForReadiness(isReady: boolean): "success" | "warning" {
  return isReady ? "success" : "warning";
}

export function Case360Tabs({ caseItem, readiness }: Case360TabsProps): JSX.Element {
  const permissions = usePermissions();
  const [activeTab, setActiveTab] = useState<CaseWorkspaceTabKey>("overview");
  const [currentReadiness, setCurrentReadiness] = useState(readiness);
  const { data, loading, error, refresh } = useCaseWorkspace(caseItem.id);
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    setCurrentReadiness(readiness);
  }, [readiness]);

  const reviewTarget = currentReadiness.targets.find((target) => target.target_status === "attorney_review");
  const submissionTarget = currentReadiness.targets.find((target) => target.target_status === "ready_for_submission");
  const missingDocs = currentReadiness.summary.missing_required_document_types.length;
  const currentDocuments = data?.documents.filter((document) => document.is_current) ?? [];

  const tabs = [
    { key: "overview", label: "Overview" },
    { key: "questionnaire", label: "Questionnaire", badge: data?.questionnaire?.sections.length ?? 0 },
    { key: "documents", label: "Documents", badge: currentDocuments.length },
    { key: "canonical-fields", label: "Canonical Fields", badge: data?.canonicalFields.length ?? 0 },
    { key: "inconsistencies", label: "Inconsistencies", badge: data?.inconsistencies.length ?? 0 },
    { key: "reviews", label: "Reviews", badge: data?.reviews.length ?? 0 },
    { key: "forms", label: "Forms", badge: data?.forms.length ?? 0 },
    { key: "packet", label: "Packet", badge: data?.packet ? data.packet.packet_version : 0 },
    {
      key: "readiness",
      label: "Readiness",
      badge: currentReadiness.targets.filter((target) => !target.is_ready).length,
    },
    { key: "submission", label: "Submission", badge: data?.submission?.status ? 1 : 0 },
    { key: "timeline", label: "Timeline", badge: data?.timeline.length ?? 0 },
  ].filter((item) => permissions.canAccessCaseSection(item.key as CaseWorkspaceTabKey));

  const validTabKeys = new Set<CaseWorkspaceTabKey>(tabs.map((item) => item.key as CaseWorkspaceTabKey));

  function normalizeTab(value: string | null): CaseWorkspaceTabKey {
    if (!value) {
      return tabs[0]?.key as CaseWorkspaceTabKey ?? "overview";
    }
    return validTabKeys.has(value as CaseWorkspaceTabKey)
      ? (value as CaseWorkspaceTabKey)
      : ((tabs[0]?.key as CaseWorkspaceTabKey) ?? "overview");
  }

  useEffect(() => {
    const nextTab = normalizeTab(searchParams.get("tab"));
    setActiveTab((current) => (current === nextTab ? current : nextTab));
  }, [searchParams]);

  function handleTabChange(key: CaseWorkspaceTabKey): void {
    setActiveTab(key);
    const params = new URLSearchParams(searchParams.toString());
    if (key === "overview") {
      params.delete("tab");
    } else {
      params.set("tab", key);
    }
    const nextUrl = params.toString() ? `${pathname}?${params.toString()}` : pathname;
    startTransition(() => {
      router.replace(nextUrl, { scroll: false });
    });
  }

  return (
    <div className="page-stack">
      <Card>
        <div className="case-hero">
          <div>
            <div className="case-hero__badges">
              <Badge tone="info">{caseItem.case_type}</Badge>
              <Badge tone="neutral">{caseItem.case_number}</Badge>
              <Badge tone={toneForReadiness(Boolean(reviewTarget?.is_ready))}>
                {reviewTarget?.is_ready ? "Attorney review ready" : "Attorney review blocked"}
              </Badge>
              <Badge tone={toneForReadiness(Boolean(submissionTarget?.is_ready))}>
                {submissionTarget?.is_ready ? "Submission ready" : "Submission blocked"}
              </Badge>
            </div>
            <h3>{caseItem.title}</h3>
            <p>{caseItem.summary ?? "No summary has been captured for this case yet."}</p>
          </div>
          <div className="case-hero__metrics">
            <div>
              <strong>{currentDocuments.length}</strong>
              <span>Current documents</span>
            </div>
            <div>
              <strong>{missingDocs}</strong>
              <span>Missing required docs</span>
            </div>
            <div>
              <strong>{currentReadiness.summary.open_high_or_critical_inconsistency_count}</strong>
              <span>High-risk inconsistencies</span>
            </div>
            <div>
              <strong>{currentReadiness.summary.unapproved_generated_form_count}</strong>
              <span>Forms pending approval</span>
            </div>
          </div>
        </div>
      </Card>

      <CaseQuickActions caseId={caseItem.id} />

      <Tabs items={tabs} activeKey={activeTab} onChange={(key) => handleTabChange(key as CaseWorkspaceTabKey)} />

      {loading ? <LoadingState label="Loading case workspace..." /> : null}
      {error ? (
        <ErrorState
          title="Could not load the full workspace"
          description="The core case loaded, but one or more connected sections failed to respond."
        />
      ) : null}

      {!loading && !error && data ? (
        <TabPanel>
          {activeTab === "overview" ? (
            <OverviewTab
              caseItem={caseItem}
              readiness={currentReadiness}
              data={data}
              canIssueClientPortalAccess={permissions.can("issue_client_portal_access")}
            />
          ) : null}
          {activeTab === "questionnaire" ? (
            <CaseQuestionnairePanel
              caseId={caseItem.id}
              questionnaire={data.questionnaire}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "documents" ? (
            <CaseDocumentsPanel
              caseId={caseItem.id}
              documents={data.documents}
              checklist={data.documentChecklist}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "canonical-fields" ? (
            <CanonicalFieldsPanel
              caseId={caseItem.id}
              fields={data.canonicalFields}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "inconsistencies" ? (
            <InconsistenciesPanel
              caseId={caseItem.id}
              inconsistencies={data.inconsistencies}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "reviews" ? <ReviewsTab data={data} /> : null}
          {activeTab === "forms" ? (
            <FormsPanel
              caseId={caseItem.id}
              forms={data.forms}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "packet" ? (
            <PacketPanel
              caseId={caseItem.id}
              packet={data.packet}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "readiness" ? (
            <ReadinessPanel
              caseId={caseItem.id}
              caseStatus={caseItem.status}
              readiness={currentReadiness}
              loading={loading}
              error={error}
              onValidated={setCurrentReadiness}
            />
          ) : null}
          {activeTab === "submission" ? (
            <SubmissionPanel
              caseId={caseItem.id}
              submission={data.submission}
              loading={loading}
              error={error}
              onRefresh={refresh}
            />
          ) : null}
          {activeTab === "timeline" ? (
            <TimelinePanel timeline={data.timeline} loading={loading} error={error} />
          ) : null}
        </TabPanel>
      ) : null}
    </div>
  );
}

function OverviewTab({
  caseItem,
  readiness,
  data,
  canIssueClientPortalAccess,
}: {
  caseItem: Case;
  readiness: CaseReadiness;
  data: CaseWorkspaceData;
  canIssueClientPortalAccess: boolean;
}): JSX.Element {
  const latestReview = data.reviews[0] ?? null;
  const approvedForms = data.forms.filter((form) => form.status === "approved").length;
  const resolvedInconsistencies = data.inconsistencies.filter((item) => item.status === "resolved").length;

  return (
    <div className="detail-sections">
      <Card title="Operational Summary" subtitle="A fast picture of the current case state">
        <dl className="ui-key-values">
          <div>
            <dt>Status</dt>
            <dd>{caseItem.status}</dd>
          </div>
          <div>
            <dt>Questionnaire Sections</dt>
            <dd>{data.questionnaire?.sections.length ?? 0}</dd>
          </div>
          <div>
            <dt>Approved Forms</dt>
            <dd>{approvedForms}</dd>
          </div>
          <div>
            <dt>Resolved Inconsistencies</dt>
            <dd>{resolvedInconsistencies}</dd>
          </div>
          <div>
            <dt>Attorney Approval</dt>
            <dd>{readiness.summary.attorney_approved_review_exists ? "Present" : "Missing"}</dd>
          </div>
          <div>
            <dt>Latest Review</dt>
            <dd>{latestReview ? `${latestReview.review_type} / ${latestReview.decision}` : "No review yet"}</dd>
          </div>
        </dl>
      </Card>

      <Card title="Readiness Targets" subtitle="Transition eligibility tracked by the backend">
        <div className="page-stack">
          {readiness.targets.map((target) => (
            <div key={target.target_status} className="placeholder-note">
              <strong>{target.target_status}</strong>
              <p>
                {target.is_ready ? "Ready" : "Blocked"} | {target.blockers.length} blockers | {target.warnings.length} warnings
              </p>
            </div>
          ))}
        </div>
      </Card>

      {canIssueClientPortalAccess ? (
        <ClientPortalAccessPanel caseId={caseItem.id} caseTitle={caseItem.title} />
      ) : (
        <Card title="Client Portal Access" subtitle="Access to portal issuance is limited by role.">
          <p className="entity-card__hint">Your role can view this case but cannot issue or regenerate client portal credentials.</p>
        </Card>
      )}
    </div>
  );
}

function ReviewsTab({ data }: { data: CaseWorkspaceData }): JSX.Element {
  if (!data.reviews.length) {
    return (
      <EmptyState
        title="No reviews yet"
        description="Paralegal and attorney review activity will appear here once the case starts moving through review."
      />
    );
  }

  return (
    <Card title="Reviews" subtitle="Review decisions and notes captured on the case">
      <div className="page-stack">
        {data.reviews.map((review) => (
          <div key={review.id} className="placeholder-note">
            <strong>
              {review.review_type} | {review.decision}
            </strong>
            <p>
              {review.reviewer_reference} | {formatDateTime(review.reviewed_at ?? review.created_at)}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}
