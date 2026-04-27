import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  className?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", ...props }, ref) => {
    const baseClass = `w-full rounded-lg border px-3 py-2 text-xs text-gray-800 placeholder-gray-300 outline-none transition focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 bg-white ${
      error ? "border-red-400" : "border-gray-200"
    }`;

    return (
      <div>
        {label && (
          <label className="block text-[10px] font-semibold tracking-widest text-gray-600 uppercase mb-1">
            {label}
          </label>
        )}
        <input ref={ref} className={`${baseClass} ${className}`} {...props} />
        {error && (
          <p className="text-red-500 text-[10px] mt-0.5">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
