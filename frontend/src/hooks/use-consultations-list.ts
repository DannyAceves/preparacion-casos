"use client";

import { useEffect, useState } from "react";

import { listConsultations } from "@/services/consultations";
import { Consultation } from "@/types/consultation";

interface UseConsultationsListResult {
  items: Consultation[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useConsultationsList(): UseConsultationsListResult {
  const [items, setItems] = useState<Consultation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(activeCheck?: () => boolean): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      const nextItems = await listConsultations();
      if (activeCheck && !activeCheck()) {
        return;
      }
      setItems(nextItems);
    } catch (loadError) {
      if (activeCheck && !activeCheck()) {
        return;
      }
      const message = loadError instanceof Error ? loadError.message : "Failed to load consultations.";
      setError(message);
    } finally {
      if (!activeCheck || activeCheck()) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    let active = true;
    void load(() => active);
    return () => {
      active = false;
    };
  }, []);

  return {
    items,
    loading,
    error,
    refresh: () => load(),
  };
}
