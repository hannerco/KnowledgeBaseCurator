import { useAuthStore } from "@/src/store/auth.store";

export const useRegister = () => {
  const register = useAuthStore((state) => state.register);
  const loading = useAuthStore((state) => state.loading);
  const error = useAuthStore((state) => state.error);

  return {
    register,
    loading,
    error,
  };
};
