import React from "react";

type Props = {
  title?: string;
  children: React.ReactNode;
  className?: string;
};

export default function SectionCard({ title, children, className = "" }: Props) {
  return (
    <section className={`av-card rounded-2xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}>
      {title ? <div className="mb-4 text-lg font-semibold tracking-tight text-slate-900">{title}</div> : null}
      <div>{children}</div>
    </section>
  );
}
