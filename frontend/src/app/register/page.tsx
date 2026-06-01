"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import RegisterForm from "@/src/components/auth/RegisterForm";
import { useAuthStore } from "@/src/store/auth.store";

export default function RegisterPage() {
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

  return <RegisterForm />;
}