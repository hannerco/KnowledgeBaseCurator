"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/src/store/auth.store";
import Sidebar from "@/src/components/dashboard/Sidebar";
import { createContext } from "react";
import { useLoadChats } from "@/src/hooks/useLoadChats"; 

export const SidebarContext = createContext<{
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}>({ collapsed: false, setCollapsed: () => {} });

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const loadSession = useAuthStore((state) => state.loadSession);

  useLoadChats();

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  useEffect(() => {
    if (!token) {
      router.push("/login");
    }
  }, [token, router]);

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f0f5ff]">
        <div className="text-gray-400 text-sm">Cargando...</div>
      </div>
    );
  }

  return (
    <SidebarContext.Provider value={{ collapsed, setCollapsed }}>
      <div className="flex min-h-screen overflow-hidden bg-[#f0f5ff]">
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <main
          className={`
            flex-1 min-h-screen overflow-x-hidden
            pb-20 md:pb-0
            transition-all duration-300 ease-in-out
            ${collapsed ? "md:ml-16" : "md:ml-52"}
          `}
        >
          {children}
        </main>
      </div>
    </SidebarContext.Provider>
  );
}