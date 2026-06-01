import { FiPlus } from "react-icons/fi";

import { Button } from "@/src/components/ui/Button";
import { Input } from "@/src/components/ui/Input";

interface ExamCreateCardProps {
  title: string;
  description: string;
  loading: boolean;
  onTitleChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onCreate: () => void;
}

export function ExamCreateCard({
  title,
  description,
  loading,
  onTitleChange,
  onDescriptionChange,
  onCreate,
}: ExamCreateCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <FiPlus className="text-blue-950" />
        <h2 className="text-sm font-semibold text-[#1a2b4a]">Nuevo examen</h2>
      </div>
      <p className="text-[11px] text-gray-400 mb-3">
        Crea el examen y luego selecciona la clave base.
      </p>
      <div className="space-y-3">
        <Input
          label="Titulo"
          placeholder="Parcial 1"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
        />
        <div>
          <label className="block text-[10px] font-semibold tracking-widest text-gray-600 uppercase mb-1">
            Descripcion
          </label>
          <textarea
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
            placeholder="Opcional"
            className="w-full rounded-lg border px-3 py-2 text-xs text-gray-800 placeholder-gray-300 outline-none transition focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white border-gray-200 min-h-[72px]"
          />
        </div>
        <Button isLoading={loading} onClick={onCreate}>
          Crear examen
        </Button>
      </div>
    </div>
  );
}
