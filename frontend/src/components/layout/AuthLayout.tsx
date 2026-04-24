"use client";
import React from "react";
import { AuthHeader } from "./AuthHeader";

interface AuthLayoutProps {
  children: React.ReactNode;
  title?: string;
  loginLink?: string;
  showSidebar?: boolean;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title = "SchoolAI",
  loginLink = "/login",
  showSidebar = true,
}) => {
  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <AuthHeader title={title} loginLink={loginLink} />

      <main className="flex flex-1 overflow-hidden">
        
        {showSidebar && (
          <div className="bg-blue-950 h-full w-1/2 hidden md:flex flex-col items-center justify-center gap-6 px-12" />
        )}

        <div
          className={`h-full w-full ${
            showSidebar ? "md:w-1/2" : "w-full"
          } flex flex-col items-center justify-center bg-sky-50 px-6 overflow-y-auto`}
        >
          {children}
        </div>
      </main>
    </div>
  );
};
