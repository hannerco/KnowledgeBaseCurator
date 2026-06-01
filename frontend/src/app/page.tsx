"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { RiGraduationCapLine } from "react-icons/ri";
import { SoftServeLogo } from "@/src/components/ui/SoftServeLogo";
import { useAuthStore } from "@/src/store/auth.store";

export default function Home() {
  const router = useRouter();
  const token = useAuthStore((state) => state.token);
  const loadSession = useAuthStore((state) => state.loadSession);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  useEffect(() => {
    if (token) {
      router.push("/dashboard");
    }
  }, [token, router]);

  if (token) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#f0f4ff] font-sans flex flex-col">

      <header className="bg-white">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 md:p-4 lg:px-8">
          <div className="flex items-center gap-x-3">
            <RiGraduationCapLine className="h-8 w-auto text-white p-2 rounded bg-blue-950" />
            <span className="text-lg font-bold text-indigo-900">SchoolAI</span>
          </div>
          <div className="flex items-center gap-x-3 md:gap-x-6">
            <h3 className="text-sm font-normal text-gray-400 hidden lg:block">¿ya tienes cuenta?</h3>
            <Link href="/login" className="text-sm font-semibold text-indigo-900">Iniciar sesión</Link>
            <Link href="/register" className="text-sm font-semibold bg-blue-950 text-white px-4 py-2 md:px-5 rounded-lg hover:bg-blue-900 transition-colors shadow-md">
              Regístrate
            </Link>
          </div>
        </nav>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-5 md:px-10 pt-8 md:pt-8 pb-5 md:pb-14 flex flex-col md:flex-row items-center gap-10 md:gap-16">
        <div className="flex-1 flex flex-col gap-5 md:gap-6 text-center md:text-left items-center md:items-start">
          <span className="inline-flex items-center w-fit gap-2 bg-indigo-100 text-indigo-700 text-xs font-semibold tracking-widest uppercase px-4 py-2 rounded-full border border-indigo-200">
            The Digital Atelier
          </span>
          <h1 className="text-4xl sm:text-5xl md:text-5xl font-extrabold text-blue-950 leading-[1.08] tracking-tight">
            Ayuda para el<br />
            pensamiento y la<br />
            educación del futuro
          </h1>
          <p className="text-gray-500 text-base md:text-lg leading-relaxed max-w-md">

            Agente digital de apoyo docente que sintetiza conocimiento y potencia la enseñanza
            a través de IA generativa de alta precisión.
          </p>
          <div className="flex flex-col sm:flex-row items-center gap-3 mt-1 w-full sm:w-auto">
            <Link href="/login" className="w-full sm:w-auto text-center bg-blue-950 text-white font-semibold px-7 py-3.5 rounded-xl hover:bg-blue-900 transition-all shadow-lg hover:-translate-y-0.5 duration-200">
              Empezar ahora
            </Link>
            <Link href="/login" className="w-full sm:w-auto text-center bg-white text-blue-950 font-semibold px-7 py-3.5 rounded-xl border border-blue-200 hover:bg-indigo-50 transition-all duration-200">
              Explorar metodología
            </Link>
          </div>
        </div>

        <div className="flex-1 flex justify-center w-full max-w-sm md:max-w-lg">
          <div className="relative w-full aspect-[4/3] rounded-3xl overflow-hidden shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-900" />
            <div className="absolute inset-0 flex items-center justify-center opacity-20">
              <div className="w-64 h-64 bg-cyan-400 rounded-full blur-3xl" />
            </div>
            <div className="absolute inset-0 opacity-10"
              style={{ backgroundImage: "linear-gradient(rgba(100,200,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(100,200,255,0.5) 1px, transparent 1px)", backgroundSize: "40px 40px" }}
            />
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
              <div className="w-14 h-14 md:w-16 md:h-16 bg-cyan-400/20 border border-cyan-400/40 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#67e8f9" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" />
                </svg>
              </div>
              <p className="text-cyan-300/70 text-xs tracking-widest uppercase font-medium">School AI Engine</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-5 md:px-10 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">

          <div className="flex items-center gap-2 text-sm text-gray-400">
            <RiGraduationCapLine className="h-5 w-5 text-blue-950" />
            <span className="font-semibold text-gray-600">SchoolAI</span>
            <span>·</span>
            <span>Plataforma de apoyo docente</span>
          </div>

          <a
            href="https://www.softserveinc.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2.5 group"
            title="Visitar SoftServe"
          >
            <span className="text-xs text-gray-400 font-medium">Desarrollado con</span>
            <div className="flex items-center gap-2 bg-gray-900 hover:bg-gray-800 transition-colors px-3 py-1.5 rounded-lg">
              <div className="w-5 h-5 flex items-center justify-center">
                <SoftServeLogo size={18} />
              </div>
              <span className="text-white text-xs font-bold tracking-wide">SoftServe</span>
            </div>
          </a>

        </div>
      </footer>

    </div>
  );
}
