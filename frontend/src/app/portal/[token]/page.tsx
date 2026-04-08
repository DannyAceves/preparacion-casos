import { ClientPortalShell } from "@/components/portal/client-portal-shell";

interface ClientPortalPageProps {
  params: {
    token: string;
  };
}

export default function ClientPortalPage({ params }: ClientPortalPageProps): JSX.Element {
  return <ClientPortalShell token={params.token} />;
}
