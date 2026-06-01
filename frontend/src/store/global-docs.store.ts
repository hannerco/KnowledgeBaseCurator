import { create } from "zustand";
import { persist } from "zustand/middleware";

interface GlobalDocsState {
  selectedGlobalDocs: string[];

  toggleGlobalDoc: (id: string) => void;

  clearSelectedGlobalDocs: () => void;

  setSelectedGlobalDocs: (ids: string[]) => void;
}

export const useGlobalDocsStore = create<GlobalDocsState>()(
  persist(
    (set) => ({
      selectedGlobalDocs: [],

      toggleGlobalDoc: (id) =>
        set((state) => ({
          selectedGlobalDocs: state.selectedGlobalDocs.includes(id)
            ? state.selectedGlobalDocs.filter((docId) => docId !== id)
            : [...state.selectedGlobalDocs, id],
        })),

      clearSelectedGlobalDocs: () =>
        set({
          selectedGlobalDocs: [],
        }),

      setSelectedGlobalDocs: (ids) =>
        set({
          selectedGlobalDocs: ids,
        }),
    }),
    {
      name: "schoolai-global-docs",
    }
  )
);