"use client";

import React, { useState } from "react";

type Props = {
  label: string;
  message: string;
  onConfirm: () => Promise<void> | void;
  className?: string;
};

export default function ConfirmDelete({ label, message, onConfirm, className = "" }: Props) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    const confirmed = window.confirm(message);
    if (!confirmed) {
      return;
    }

    setLoading(true);
    try {
      await onConfirm();
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className={`inline-flex items-center rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700 shadow-sm transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-70 ${className}`}
    >
      {loading ? "Eliminando..." : label}
    </button>
  );
}
