"use client";
import { useState } from "react";
import { RiGraduationCapLine } from "react-icons/ri";
import { AuthLayout } from "../layout/AuthLayout";
import { Input, Button, Alert, Checkbox, Divider } from "../ui";


type LoginFormData = {
    email: string;
    password: string;
};

const INITIAL_FORM: LoginFormData = {
    email: "",
    password: "",
}


export default function LoginForm(){
    const [form, setForm] = useState<LoginFormData>(INITIAL_FORM);
    const [errors, setErrors] = useState<Partial<Record<keyof LoginFormData, string>>>({});
    const [statusMessage, setStatusMessage] = useState("");
    const [loading, setLoading] = useState(false);

    const handleChage = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;
        setForm((prev) => ({
            ...prev,
            [name]: value,
        }));
        setErrors((prev) => ({ ...prev, [name]: "" }));
        setStatusMessage("");
    }

    const validate = () => {
        const newErrors: Partial<Record<keyof LoginFormData, string>> = {};
        if (!form.email.includes("@")) newErrors.email = "Ingresa un correo válido.";
        if (form.password.length < 6) newErrors.password = "Contraseña muy corta.";
        return newErrors;
    }

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
            setStatusMessage("Validación completada. Aquí irá la integración con la API.");
        }, 500);
    }

    return (
        <AuthLayout
            headerText=""
            linkText=""
            loginLink="/register"
        >
            Hola
        </AuthLayout>
    
    )
}
