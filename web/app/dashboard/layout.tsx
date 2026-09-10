import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { signOutAction } from "./actions";

export default async function DashboardLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const { email } = await requireUser();
  return (
    <div className="dashboard">
      <header className="container nav">
        <Link className="brand" href="/dashboard">Trace<span>RAG</span></Link>
        <div className="row">
          <span className="muted small">{email}</span>
          <form action={signOutAction}><button className="button" type="submit">Sign out</button></form>
        </div>
      </header>
      {children}
    </div>
  );
}
