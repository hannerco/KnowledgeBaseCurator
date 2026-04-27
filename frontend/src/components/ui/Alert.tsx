import React from "react";

interface AlertProps {
  message: string;
  type?: "error" | "success" | "warning";
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({ message, type = "error", className = "" }) => {
  const typeStyles = {
    error: "bg-red-50 border-red-200 text-red-600",
    success: "bg-green-50 border-green-200 text-green-600",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-600",
  };

  return (
    <div
      className={`rounded-lg border px-3 py-2 text-xs ${typeStyles[type]} ${className}`}
      role="alert"
    >
      {message}
    </div>
  );
};
