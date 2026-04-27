import { RegisterPayload, RegisterResponse } from "../types/auth.types";

export const authService = {
  register: async (payload: RegisterPayload): Promise<RegisterResponse> => {
    console.warn("authService.register: backend aún no conectado.", payload);
    return new Promise((resolve) => {
      setTimeout(() => resolve({ message: "Simulación local: backend pendiente." }), 300);
    });
  },
};