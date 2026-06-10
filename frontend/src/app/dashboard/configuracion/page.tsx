"use client";

import { useAuthStore } from "@/src/store/auth.store";
import { useRouter } from "next/navigation";
import { FiUser, FiMail, FiSun, FiShield, FiChevronRight, FiHelpCircle } from "react-icons/fi";
import { resetTour } from "@/src/tour/useTour";

// Cambia a true cuando se quiera hacer el modo oscuro
const FEATURE_DARK_MODE = false;

export default function ConfiguracionPage() {
  const user = useAuthStore((state) => state.user);
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#f0f5ff] p-4 pt-16 md:p-8">
      <div className="max-w-4xl mx-auto">

        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[#1a2b4a]">Configuración</h1>
          <p className="text-sm text-gray-400 mt-1">Administra tu perfil y preferencias.</p>
        </div>

        <div className="space-y-5">

          <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-50">
              <h2 className="text-sm font-semibold text-[#1a2b4a] flex items-center gap-2">
                <FiUser className="h-4 w-4 text-blue-500" />
                Perfil
              </h2>
            </div>

            <div className="px-6 py-5 space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-blue-950 flex items-center justify-center text-white text-xl font-bold shrink-0">
                  {user?.name?.charAt(0).toUpperCase() ?? "U"}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-800">{user?.name ?? "Usuario"}</p>
                  <p className="text-xs text-gray-400">{user?.email ?? "—"}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Nombre completo</label>
                  <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5">
                    <FiUser className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                    <span className="text-sm text-gray-600">{user?.name ?? "—"}</span>
                  </div>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-400 mb-1 block">Correo electrónico</label>
                  <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5">
                    <FiMail className="h-3.5 w-3.5 text-gray-400 shrink-0" />
                    <span className="text-sm text-gray-600 truncate">{user?.email ?? "—"}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {FEATURE_DARK_MODE && (
            <section className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-50">
                <h2 className="text-sm font-semibold text-[#1a2b4a] flex items-center gap-2">
                  <FiSun className="h-4 w-4 text-blue-500" />
                  Apariencia
                </h2>
              </div>
              <div className="px-6 py-5 space-y-4">
                <div className="flex gap-3">
                  <button className="flex-1 flex flex-col items-center gap-2 p-3 rounded-xl border-2 border-blue-500 bg-blue-50 transition-all">
                    <div className="w-full h-10 bg-white rounded-lg border border-gray-200 flex items-center px-2 gap-1">
                      <div className="w-2 h-2 rounded-full bg-gray-300" />
                      <div className="flex-1 h-1.5 bg-gray-200 rounded" />
                    </div>
                    <span className="text-xs font-medium text-blue-700">Claro</span>
                  </button>
                  <button className="flex-1 flex flex-col items-center gap-2 p-3 rounded-xl border-2 border-gray-200 transition-all">
                    <div className="w-full h-10 bg-gray-800 rounded-lg border border-gray-700 flex items-center px-2 gap-1">
                      <div className="w-2 h-2 rounded-full bg-gray-600" />
                      <div className="flex-1 h-1.5 bg-gray-700 rounded" />
                    </div>
                    <span className="text-xs font-medium text-gray-500">Oscuro</span>
                  </button>
                </div>
              </div>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}
