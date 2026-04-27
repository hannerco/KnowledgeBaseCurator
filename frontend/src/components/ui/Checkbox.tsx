import React from "react";

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
  error?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, error, className = "", ...props }, ref) => {
    return (
      <div>
        <label className="flex items-start gap-2 cursor-pointer select-none">
          <input
            ref={ref}
            type="checkbox"
            className={`mt-0.5 h-3 w-3 accent-blue-700 cursor-pointer ${className}`}
            {...props}
          />
          <span className="text-xs text-gray-400 leading-relaxed">{label}</span>
        </label>
        {error && (
          <p className="text-red-500 text-[10px] mt-0.5">{error}</p>
        )}
      </div>
    );
  }
);

Checkbox.displayName = "Checkbox";
