"use client";

import React from "react";
import Sidebar from "../layout/Sidebar";
import Topbar from "../layout/Topbar";

type Props = {
  children: React.ReactNode;
};

export default function AuthLayout({ children }: Props) {
  return (
    <div className="min-h-screen bg-slate-100">
      <Sidebar />
      <div className="ml-64 flex min-h-screen min-w-0 flex-col">
        <Topbar />
        <main className="min-w-0 flex-1 px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
