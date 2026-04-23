"use client";
import { RiGraduationCapLine } from "react-icons/ri";
import { LiaUniversitySolid } from "react-icons/lia";
import { useState } from "react";

export default function Register() {
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Form submitted:", form);
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <header className="bg-white shadow h-auto shrink-0">
        <nav
          aria-label="Global"
          className="mx-auto flex max-w-7xl items-center justify-between p-4 lg:px-8"
        >
          <div className="flex items-center lg:flex-1 gap-x-3">
            <RiGraduationCapLine className="h-8 w-auto text-white p-2 rounded bg-blue-950" />
            <h1 className="text-lg font-bold text-indigo-900">SchoolAI</h1>
          </div>

          <div className="flex items-center gap-x-6">
            <h3 className="text-sm font-normal text-gray-400">
              ¿ya tienes cuenta?
            </h3>
            <div className="hidden lg:flex lg:flex-1 lg:justify-end">
              <a href="#" className="text-sm/6 font-semibold text-indigo-900">
                inicia sesión
              </a>
            </div>
          </div>
        </nav>
      </header>

      <main className="flex flex-1 overflow-hidden">
        <div className="bg-blue-950 h-full w-1/2 hidden md:flex flex-col items-center justify-center gap-6 px-12" />

        <div className="h-full w-full md:w-1/2 flex flex-col items-center justify-center bg-sky-50 px-6 overflow-y-auto">
          <div className="w-full max-w-md">

            <div className="text-center mb-4">
              <h1 className="text-2xl font-semibold text-blue-900 tracking-tight">
                Únete al SchoolAI
              </h1>
              <p className="text-gray-400 mt-0.5 text-xs">
                Crea tu chat personal
              </p>
            </div>

            <div className="px-10 py-1">
              <form onSubmit={handleSubmit} className="space-y-3">
                <div>
                  <label className="block text-[10px] font-semibold tracking-widest text-gray-600 uppercase mb-1">
                    Nombre Completo
                  </label>
                  <input
                    name="fullName"
                    type="text"
                    placeholder="Ej. Dr. Alejandro Voss"
                    value={form.fullName}
                    onChange={handleChange}
                    className="w-full rounded-lg border px-3 py-2 text-xs text-gray-800 placeholder-gray-300 outline-none transition focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 border-gray-200 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-semibold tracking-widest text-gray-600 uppercase mb-1">
                    Correo Institucional
                  </label>
                  <input
                    name="email"
                    type="text"
                    placeholder="nombre@universidad.edu"
                    value={form.email}
                    onChange={handleChange}
                    className="w-full rounded-lg border px-3 py-2 text-xs text-gray-800 placeholder-gray-300 outline-none transition focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 border-gray-200 bg-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-semibold tracking-widest text-gray-600 uppercase mb-1">
                      Contraseña
                    </label>
                    <input
                      name="password"
                      type="password"
                      placeholder="••••••••"
                      value={form.password}
                      onChange={handleChange}
                      className="w-full rounded-lg border px-3 py-2 text-xs text-gray-800 placeholder-gray-300 outline-none transition focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 border-gray-200 bg-white"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-semibold tracking-widest text-gray-600 uppercase mb-1">
                      Confirmar Contraseña
                    </label>
                    <input
                      name="confirmPassword"
                      type="password"
                      placeholder="••••••••"
                      value={form.confirmPassword}
                      onChange={handleChange}
                      className="w-full rounded-lg border px-3 py-2 text-xs text-gray-800 placeholder-gray-300 outline-none transition focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 border-gray-200 bg-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="flex items-start gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      name="acceptTerms"
                      checked={form.acceptTerms}
                      onChange={handleChange}
                      className="mt-0.5 h-3 w-3 accent-blue-700 cursor-pointer"
                    />
                    <span className="text-xs text-gray-400 leading-relaxed">
                      Acepto los{" "}
                      <a href="#" className="text-blue-900 ">
                        Términos de Servicio
                      </a>{" "}
                      y la{" "}
                      <a href="#" className="text-blue-900">
                        Política de Investigación Ética
                      </a>.
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  className="w-full bg-blue-950 hover:bg-blue-900 active:scale-[0.98] text-white font-semibold text-sm rounded-lg py-2 transition-all duration-150 shadow-md hover:shadow-lg">
                  Crear Cuenta
                </button>
              </form>

              <div className="flex items-center gap-3 my-2.5">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-[10px] font-semibold tracking-widest text-gray-600 uppercase">
                  O continuar con
                </span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button className="flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 text-xs font-medium text-gray-600 bg-white hover:bg-indigo-950 hover:text-white active:scale-[0.98] transition-all duration-150">
                  <LiaUniversitySolid />
                  correo universitario
                </button>

                <button className="flex items-center justify-center gap-2 border border-gray-200 rounded-lg py-2 text-xs font-medium text-gray-600 bg-white hover:bg-indigo-950 hover:text-white active:scale-[0.98] transition-all duration-150">
                  <RiGraduationCapLine />
                  ID
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}