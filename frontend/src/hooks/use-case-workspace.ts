"use client";

import { useEffect, useState } from "react";

import { getCaseWorkspace } from "@/services/workspace";
import { ApiErrorPayload } from "@/types/api";
import { CaseWorkspaceData } from "@/types/workspace";

interface UseCaseWorkspaceState {
  data: CaseWorkspaceData | null;
  loading: boolean;
  error: ApiErrorPayload | null;
  refresh: () => Promise<void>;
}

export function useCaseWorkspace(caseId: string): UseCaseWorkspaceState {
  const [data, setData] = useState<CaseWorkspaceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiErrorPayload | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadWorkspace(): Promise<void> {
      setLoading(true);
      setError(null);

      try {
        const nextData = await getCaseWorkspace(caseId);
        if (!cancelled) {
          setData(nextData);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError as ApiErrorPayload);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadWorkspace();

    return () => {
      cancelled = true;
    };
  }, [caseId]);

  async function refresh(): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      const nextData = await getCaseWorkspace(caseId);
      setData(nextData);
    } catch (loadError) {
      setError(loadError as ApiErrorPayload);
    } finally {
      setLoading(false);
    }
  }

  return { data, loading, error, refresh };
}
