"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthLayout } from "../layout/AuthLayout";
import { Input, Button, Alert } from "../ui";
import { useRegister } from "@/src/hooks/useRegister";

type RegisterFormData = { fullName: string; email: string; password: string; confirmPassword: string };
const INITIAL_FORM: RegisterFormData = { fullName: "", email: "", password: "", confirmPassword: "" };

export default function RegisterForm() {
  const router  = useRouter();
  const [form, setForm]                     = useState<RegisterFormData>(INITIAL_FORM);
  const [errors, setErrors]                 = useState<Partial<Record<keyof RegisterFormData, string>>>({});
  const [statusMessage, setStatusMessage]   = useState("");
  const [loading, setLoading]               = useState(false);
  const { register, loading: authLoading, error: authError } = useRegister();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
    setStatusMessage("");
  };

  const validate = () => {
    const newErrors: Partial<Record<keyof RegisterFormData, string>> = {};
    if (!form.fullName.trim())                 newErrors.fullName        = "El nombre es requerido.";
    if (!form.email.includes("@"))             newErrors.email           = "Ingresa un correo válido.";
    if (form.password.length < 6)              newErrors.password        = "Mínimo 6 caracteres.";
    if (form.password !== form.confirmPassword) newErrors.confirmPassword = "Las contraseñas no coinciden.";
    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const newErrors = validate();
    if (Object.keys(newErrors).length > 0) { setErrors(newErrors); return; }
    setLoading(true);
    try {
      const message = await register({ name: form.fullName, email: form.email, password: form.password });
      setStatusMessage(message);
      router.push("/login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="w-full max-w-md">
        <div className="text-center mb-4">
          <h1 className="text-2xl font-semibold text-blue-900 tracking-tight">Únete al SchoolAI</h1>
          <p className="text-gray-400 mt-0.5 text-xs">Crea tu chat personal</p>
        </div>

        <div className="px-5 sm:px-10 py-6 sm:py-8 bg-white rounded-2xl shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-3" noValidate>
            {statusMessage && <Alert message={statusMessage} type="success" />}
            {authError      && <Alert message={authError}   type="error"   />}

            <Input name="fullName" type="text"  placeholder="Ej: Dr. Alejandro Voss"      label="Nombre Completo"     value={form.fullName} onChange={handleChange} error={errors.fullName} />
            <Input name="email"    type="email"  placeholder="nombre@universidad.edu"      label="Correo Institucional" value={form.email}    onChange={handleChange} error={errors.email}    />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 md:gap-3">
              <Input name="password"        type="password" placeholder="••••••••" label="Contraseña"         value={form.password}        onChange={handleChange} error={errors.password}        />
              <Input name="confirmPassword" type="password" placeholder="••••••••" label="Confirmar Contraseña" value={form.confirmPassword} onChange={handleChange} error={errors.confirmPassword} />
            </div>

            <Button type="submit" isLoading={loading || authLoading} variant="primary">
              {loading || authLoading ? "Validando datos..." : "Crear Cuenta"}
            </Button>
          </form>
        </div>

        <div className="py-5 flex flex-row items-center justify-center gap-2">
          <span className="text-sm font-normal text-gray-600">¿Ya tienes una cuenta?</span>
          <a href="/login" className="text-sm font-normal text-blue-950 hover:text-blue-800 transition-colors">Inicia sesión</a>
        </div>
      </div>
    </AuthLayout>
  );
}
