import React from "react";

type Props = {
  children: React.ReactNode;
  title?: string;
  className?: string;
};

export default function PageContainer({ children, title, className = "" }: Props) {
  return (
    <div className={`mx-auto flex w-full max-w-7xl flex-col gap-6 ${className}`}>
      {title ? <h2 className="text-3xl font-semibold tracking-tight text-slate-900">{title}</h2> : null}
      <div className="space-y-6">{children}</div>
    </div>
  );
}
