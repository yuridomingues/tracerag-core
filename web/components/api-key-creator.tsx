"use client";

import { useState } from "react";

export function ApiKeyCreator({ projectId }: { projectId: string }) {
  const [token, setToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function createKey() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/projects/${projectId}/keys`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: "CI key" }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Could not create API key.");
      setToken(body.token);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create API key.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stack">
      <p className="muted small">
        Keys are stored only as SHA-256 hashes. The full token is shown once.
      </p>
      <button className="button" type="button" onClick={createKey} disabled={loading}>
        {loading ? "Creating…" : "Create CI API key"}
      </button>
      {token ? <div><p className="small">Copy this token now:</p><div className="token code">{token}</div></div> : null}
      {error ? <div className="notice error">{error}</div> : null}
    </div>
  );
}
