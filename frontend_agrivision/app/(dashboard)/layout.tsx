import React from "react";
import AuthLayout from "../../components/layout/AuthLayout";
import ProtectedRoute from "../../components/auth/ProtectedRoute";

export const metadata = {
  title: "AgriVision - Dashboard",
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AuthLayout>{children}</AuthLayout>
    </ProtectedRoute>
  );
}
