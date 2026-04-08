interface PortalIndexPageProps {
  searchParams?: {
    notice?: string;
  };
}

export default function PortalIndexPage({ searchParams }: PortalIndexPageProps): JSX.Element {
  const wasRedirectedFromInternalWorkspace = searchParams?.notice === "internal-workspace-unavailable";

  return (
    <main className="login-page">
      <div className="login-page__hero">
        <p className="app-header__label">Client Portal</p>
        <h1 className="app-header__title">Secure Access Required</h1>
        <p>
          Open the secure portal link shared for your case to continue with your questionnaire, checklist and
          document uploads.
        </p>
        {wasRedirectedFromInternalWorkspace ? (
          <p className="document-feedback document-feedback--error">
            Your account can only use the secure client portal. The page you tried to open is not available for
            client access.
          </p>
        ) : null}
      </div>
    </main>
  );
}
