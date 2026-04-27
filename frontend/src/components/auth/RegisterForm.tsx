"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { LiaUniversitySolid } from "react-icons/lia";
import { RiGraduationCapLine } from "react-icons/ri";
import { AuthLayout } from "../layout/AuthLayout";
import { Input, Button, Alert, Checkbox, Divider } from "../ui";

type RegisterFormData = {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
};

type RegisterFormProps = {
  showAlternativeAuth?: boolean;
};

const INITIAL_FORM: RegisterFormData = {
  fullName: "",
  email: "",
  password: "",
  confirmPassword: "",
  acceptTerms: false,
};

export default function RegisterForm({ showAlternativeAuth = false }: RegisterFormProps) {  const router = useRouter();  const [form, setForm] = useState<RegisterFormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof RegisterFormData, string>>>({});
  const [statusMessage, setStatusMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    setErrors((prev) => ({ ...prev, [name]: "" }));
    setStatusMessage("");
  };

  const validate = () => {
    const newErrors: Partial<Record<keyof RegisterFormData, string>> = {};

    if (!form.fullName.trim()) newErrors.fullName = "El nombre es requerido.";
    if (!form.email.includes("@")) newErrors.email = "Ingresa un correo válido.";
    if (form.password.length < 6) newErrors.password = "Mínimo 6 caracteres.";
    if (form.password !== form.confirmPassword)
      newErrors.confirmPassword = "Las contraseñas no coinciden.";
    if (!form.acceptTerms) newErrors.acceptTerms = "Debes aceptar los términos.";

    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const newErrors = validate();

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setStatusMessage("");
      return;
    }

    setLoading(true);
    setStatusMessage("");

    setTimeout(() => {
      setLoading(false);
      router.push("/dashboard");
    }, 500);
  };

  return (
    <AuthLayout>
        
      <div className="w-full max-w-md mb-12">
        <div className="text-center mb-4">
          <h1 className="text-2xl font-semibold text-blue-900 tracking-tight">
            Únete al SchoolAI
          </h1>
          <p className="text-gray-400 mt-0.5 text-xs">Crea tu chat personal</p>
        </div>

        <div className="px-10 py-1">
          <form onSubmit={handleSubmit} className="space-y-3" noValidate>
            {statusMessage && <Alert message={statusMessage} type="success" />}

            <Input
              name="fullName"
              type="text"
              placeholder="Ej: Dr. Alejandro Voss"
              label="Nombre Completo"
              value={form.fullName}
              onChange={handleChange}
              error={errors.fullName}
            />

            <Input
              name="email"
              type="email"
              placeholder="nombre@universidad.edu"
              label="Correo Institucional"
              value={form.email}
              onChange={handleChange}
              error={errors.email}
            />

            <div className="grid grid-cols-2 gap-2">
              <Input
                name="password"
                type="password"
                placeholder="••••••••"
                label="Contraseña"
                value={form.password}
                onChange={handleChange}
                error={errors.password}
              />
              <Input
                name="confirmPassword"
                type="password"
                placeholder="••••••••"
                label="Confirmar Contraseña"
                value={form.confirmPassword}
                onChange={handleChange}
                error={errors.confirmPassword}
              />
            </div>

            <Checkbox
              name="acceptTerms"
              checked={form.acceptTerms}
              onChange={handleChange}
              error={errors.acceptTerms ? "Debes aceptar los términos." : ""}
              label={
                <>
                  Acepto los{" "}
                  <a href="#" className="text-blue-900">
                    Términos de Servicio
                  </a>{" "}
                  y la{" "}
                  <a href="#" className="text-blue-900">
                    Política de Investigación Ética
                  </a>
                  .
                </>
              }
            />

            <Button type="submit" isLoading={loading} variant="primary">
              {loading ? "Validando datos..." : "Crear Cuenta"}
            </Button>
          </form>

          {showAlternativeAuth && (
            <div className="mt-4">
              <Divider text="O continuar con" />

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
          )}
        </div>
      </div>
    </AuthLayout>
  );
}