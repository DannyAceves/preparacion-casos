import Link from "next/link";

export default function NotFoundPage(): JSX.Element {
  return (
    <main className="page-stack" style={{ padding: "64px" }}>
      <div className="page-heading">
        <div>
          <h2>Case not found</h2>
          <p>The requested resource does not exist or is not available yet.</p>
        </div>
      </div>
      <Link href="/cases" className="ui-badge ui-badge--info">
        Return to cases
      </Link>
    </main>
  );
}
